import pytest
from unittest.mock import Mock, call
import os
import shutil
from project_generator.domain.usecases.restore_use_case import RestoreBackupUseCase

@pytest.fixture
def restore_use_case():
    return RestoreBackupUseCase()

def test_list_backups_no_dir(restore_use_case, mocker):
    mocker.patch("os.path.isdir", return_value=False)
    result = restore_use_case.list_backups("/fake/project")
    assert result == []

def test_list_backups_empty_dir(restore_use_case, mocker):
    mocker.patch("os.path.isdir", return_value=True)
    mocker.patch("os.listdir", return_value=[])
    result = restore_use_case.list_backups("/fake/project")
    assert result == []

def test_list_backups_success_sorted(restore_use_case, mocker):
    mocker.patch("os.path.isdir", return_value=True)
    mocker.patch("os.listdir", return_value=["other", "backup_2", "backup_1"])
    mocker.patch("os.path.getmtime", side_effect=lambda p: 2 if "backup_1" in p else 1)
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))

    result = restore_use_case.list_backups("/fake/project")
    assert result == ["backup_1", "backup_2"]

def test_list_backups_os_error(restore_use_case, mocker):
    mocker.patch("os.path.isdir", return_value=True)
    mocker.patch("os.listdir", side_effect=OSError("Permission denied"))
    result = restore_use_case.list_backups("/fake/project")
    assert result == []

def test_restore_backup_not_found(restore_use_case, mocker):
    mocker.patch("os.path.isdir", return_value=False)
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))
    with pytest.raises(FileNotFoundError, match="El backup 'backup_missing' no existe"):
        restore_use_case.execute("/fake/project", "backup_missing")

def test_restore_backup_success(restore_use_case, mocker):
    mocker.patch("os.path.isdir", return_value=True)
    
    def exists_side_effect(path):
        if "infrastructure/entry_points/a2a" in path:
            return False
        if "src" in path:
            return True
        return True
        
    mocker.patch("os.path.exists", side_effect=exists_side_effect)
    mock_rmtree = mocker.patch("shutil.rmtree")
    mock_copytree = mocker.patch("shutil.copytree")
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))

    result = restore_use_case.execute("/fake/project", "backup_valid")

    assert "restaurado exitosamente" in result
    mock_rmtree.assert_called_once_with("/fake/project/src")
    mock_copytree.assert_called_once_with("/fake/project/.mcp_backups/backup_valid", "/fake/project/src")

def test_restore_backup_critical_error(restore_use_case, mocker):
    mocker.patch("os.path.isdir", return_value=True)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("shutil.rmtree")
    mocker.patch("shutil.copytree", side_effect=OSError("Disk full"))
    mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))

    with pytest.raises(RuntimeError, match="Fallo crítico al restaurar"):
        restore_use_case.execute("/fake/project", "backup_valid")
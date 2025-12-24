import os
import shutil
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class RestoreBackupUseCase:
    """Use case to list backups and restore a project from one."""

    def __init__(self):
        self._backup_dir_name = ".mcp_backups"

    def list_backups(self, project_path: str) -> List[str]:
        """Lists available backups, sorted newest first."""
        backup_root = os.path.join(project_path, self._backup_dir_name)
        if not os.path.isdir(backup_root):
            return []

        try:
            backups = sorted(
                [d for d in os.listdir(backup_root) if os.path.isdir(os.path.join(backup_root, d)) and d.startswith("backup_")],
                key=lambda d: os.path.getmtime(os.path.join(backup_root, d)),
                reverse=True
            )
            return backups
        except Exception as e:
            logger.warning(f"No se pudo listar backups en '{backup_root}': {e}")
            return []

    def execute(self, project_path: str, backup_name: str) -> str:
        backup_root = os.path.join(project_path, self._backup_dir_name)
        backup_to_restore = os.path.join(backup_root, backup_name)
        
        target_folder = "src"
        if os.path.exists(os.path.join(project_path, "infrastructure/entry_points/a2a")):
            target_folder = os.path.join("application", "settings")
            
        current_target_path = os.path.join(project_path, target_folder)

        if not os.path.isdir(backup_to_restore):
            raise FileNotFoundError(f"El backup '{backup_name}' no existe o no es un directorio válido en '{backup_root}'.")

        try:
            logger.info(f"Iniciando restauración desde backup: {backup_name}")
            logger.warning(f"Se eliminará el directorio actual: {current_target_path}")
            
            if os.path.exists(current_target_path):
                shutil.rmtree(current_target_path)
                logger.info(f"Directorio '{target_folder}' actual eliminado.")

            logger.info(f"Copiando backup '{backup_name}' a '{target_folder}'...")
            shutil.copytree(backup_to_restore, current_target_path)

            success_message = f"Proyecto restaurado exitosamente desde el backup '{backup_name}'."
            logger.info(success_message)
            return success_message

        except Exception as e:
            logger.critical(f"¡FALLO CRÍTICO DURANTE LA RESTAURACIÓN DESDE {backup_name}!: {e}")
            logger.critical(f"El directorio '{target_folder}' puede estar incompleto o dañado. Revisa manualmente.")
            raise RuntimeError(f"Fallo crítico al restaurar desde '{backup_name}'. Revisa logs y el estado del directorio '{target_folder}'.") from e
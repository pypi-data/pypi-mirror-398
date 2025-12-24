## [[2.0.0](https://github.com/bancolombia/ca-scaffold-py/compare/v1.0.0...v2.0.0)] - 2025-12-19

###  

### ⚠️ Breaking Release: mandatory --type flag and agent-procode template support ([2c2b59c](https://github.com/bancolombia/ca-scaffold-py/commit/2c2b59cf9e709f2c6d9b43bd47d3b5f70a49b40a)) - Contribuidor: josealfredore2604


### BREAKING CHANGE

* ** :** The --type flag is now mandatory for project generation.
This change was necessary to support the new multi-template architecture.

- Added 'agent-procode' template with LangGraph, Kafka, and Clean Architecture.
- Restructured 'scaffold/' directory to organize templates under 'templates/mcp_server' and 'templates/agent_procode'.
- Updated CLI parsers and handlers to require the project type.
- Fixed unit tests to align with the new directory structure and mandatory arguments.

## [[1.0.0](https://github.com/bancolombia/ca-scaffold-py/compare/undefined...v1.0.0)] - 2025-11-28

###  

### 🐛 Fix Patch Release: Merge pull request #3 from bancolombia/feature/initial-scaffold-setup ([b23bb7f](https://github.com/bancolombia/ca-scaffold-py/commit/b23bb7f4fb2be8e0397f3b629d6e51da032f1058)) - Contribuidor: josealfredore2604
fixpatchrelease: Modificar pipelines

### General

- Feature: actualizando pyproject.toml ([82a32a4](https://github.com/bancolombia/ca-scaffold-py/commit/82a32a4a8e8da53a060961f32b95645392d8ec78)) - Contribuidor: Jose Ramirez
- Feature: actualizando pyproject.toml ([b79c5f2](https://github.com/bancolombia/ca-scaffold-py/commit/b79c5f2ce3c39e530fdfc7ce9248e9306f96aa04)) - Contribuidor: Jose Ramirez
- Feature: actualizando workflow ([d03fb0e](https://github.com/bancolombia/ca-scaffold-py/commit/d03fb0e607653dc488ca18a221485502660b1957)) - Contribuidor: Jose Ramirez
- Feature: actualizando workflow ([77234ba](https://github.com/bancolombia/ca-scaffold-py/commit/77234ba4fa7308c09d8a3062c080c5ad4f2a4ae7)) - Contribuidor: Jose Ramirez
- Feature: actualizando workflow ([df7d66c](https://github.com/bancolombia/ca-scaffold-py/commit/df7d66cc906fdb0e7560bf2239e706c336a50be7)) - Contribuidor: Jose Ramirez
- Feature: actualizando workflow ([7dfdd6d](https://github.com/bancolombia/ca-scaffold-py/commit/7dfdd6dc39127b1823bd5924e4161d6d2be53c6a)) - Contribuidor: Jose Alfredo Ramirez Espinosa
- Feature: actualizando workflow ([40d943b](https://github.com/bancolombia/ca-scaffold-py/commit/40d943b9dd86e3bdcd7e96cf061745f19efa65d7)) - Contribuidor: Jose Alfredo Ramirez Espinosa
- Feature: add initial scaffold generator project ([f0f28b6](https://github.com/bancolombia/ca-scaffold-py/commit/f0f28b61c93687f9b4ba36677841c3cb45eed2b0)) - Contribuidor: Jose Alfredo Ramirez Espinosa
- Add mcp_generator core functionality
- Add scaffold templates
- Add tests structure
- Add pyproject.toml and uv.lock
- Update .gitignore- Feature: Modificar pipelines ([91cfdae](https://github.com/bancolombia/ca-scaffold-py/commit/91cfdae0c71160b8cee09cbf6f4047c2d2fe0f41)) - Contribuidor: Jose Ramirez
- Feature: Modificar pipelines ([f00c0ff](https://github.com/bancolombia/ca-scaffold-py/commit/f00c0ff798dc6ed0fe89e540d2f7552472c4313e)) - Contribuidor: Jose Ramirez

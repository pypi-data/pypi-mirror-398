import json
import os
import shutil
import tempfile
from project_generator.domain.models.project_models import ProjectRequest, GeneratedProjectInfo
from cookiecutter.main import cookiecutter
from cookiecutter.exceptions import CookiecutterException

class CookiecutterAdapter:
    def generate(self, project_data: ProjectRequest, no_zip: bool = False) -> GeneratedProjectInfo:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        original_scaffold_path = os.path.join(project_root, 'scaffold')
        

        hook_util_source_in_scaffold = os.path.join(original_scaffold_path, 'hooks', 'generation_utils.py')

        temp_dir = tempfile.mkdtemp()
        generated_info = GeneratedProjectInfo(temp_dir=temp_dir)

        try:

            copied_scaffold_path = os.path.join(temp_dir, 'scaffold_template')
            shutil.copytree(original_scaffold_path, copied_scaffold_path)




            

            hook_util_source_path = os.path.join(copied_scaffold_path, 'hooks', 'generation_utils.py')
            

            hook_search_path = os.path.dirname(temp_dir)
            

            hook_util_tmp_dest_path = os.path.join(hook_search_path, 'generation_utils.py')

            if os.path.exists(hook_util_source_path):
                try:

                    shutil.copy2(hook_util_source_path, hook_util_tmp_dest_path)
                    print(f"INFO: Copiando hook utility a {hook_util_tmp_dest_path} para importación de hook.")
                except Exception as e:

                    print(f"ADVERTENCIA: No se pudo copiar hook utility a {hook_util_tmp_dest_path}: {e}")
            else:

                print(f"ADVERTENCIA CRÍTICA: No se encontró hook utility en {hook_util_source_path}. La importación del hook fallará.")



            cookiecutter_json_path = os.path.join(copied_scaffold_path, 'cookiecutter.json')
            try:
                with open(cookiecutter_json_path, 'r') as f:
                    config_data = json.load(f)
                

                config_data['dynamic_tools'] = "[]"
                config_data['dynamic_prompts'] = "[]"
                config_data['dynamic_resources'] = "[]"
                config_data['mcp_connections_json'] = "[]"

                with open(cookiecutter_json_path, 'w') as f:
                    json.dump(config_data, f, indent=4)
            except Exception as e:
                print(f"ADVERTENCIA: No se pudo modificar cookiecutter.json: {e}")


            output_dir_temp = os.path.join(temp_dir, 'output')
            os.makedirs(output_dir_temp)

            project_slug = project_data.project_name.lower().replace(' ', '_').replace('-', '_')


            extra_context = {
                "project_name": project_data.project_name,
                "project_slug": project_slug, 
                "project_type": project_data.project_type, 
                "mcp_connections_json": json.dumps(project_data.mcp_connections), 
                "dynamic_tools": json.dumps(project_data.dynamic_tools),
                "dynamic_prompts": json.dumps(project_data.dynamic_prompts),
                "dynamic_resources": json.dumps(project_data.dynamic_resources)
            }


            cookiecutter(
                template=copied_scaffold_path,
                no_input=True,
                extra_context=extra_context,
                output_dir=output_dir_temp,
                replay=False,
                overwrite_if_exists=True
            )



            project_output_path_temp = os.path.join(output_dir_temp, project_slug)

            if not os.path.exists(project_output_path_temp):

                 raise RuntimeError(f"El directorio del proyecto generado no se encontró en: {project_output_path_temp}. Revisa el hook post_gen_project.py.")


            if no_zip:
                generated_info.output_path = project_output_path_temp
            else:
                zip_base_name = os.path.join(temp_dir, project_slug)
                shutil.make_archive(
                    base_name=zip_base_name,
                    format='zip',
                    root_dir=output_dir_temp,
                    base_dir=project_slug
                )
                generated_info.zip_path = f"{zip_base_name}.zip"
                generated_info.zip_filename = f"{project_slug}.zip"


            try:
                if os.path.exists(hook_util_tmp_dest_path):
                    os.remove(hook_util_tmp_dest_path)
                    print(f"INFO: Limpiando {hook_util_tmp_dest_path}")
            except Exception as e:
                print(f"ADVERTENCIA: No se pudo limpiar {hook_util_tmp_dest_path}: {e}")

            return generated_info

        except (CookiecutterException, OSError, IOError, RuntimeError) as e:

            try:
                if os.path.exists(hook_util_tmp_dest_path):
                    os.remove(hook_util_tmp_dest_path)
            except Exception:
                pass
            
            if os.path.exists(temp_dir):
                 shutil.rmtree(temp_dir)
            print(f"Error detallado en CookiecutterAdapter: {type(e).__name__} - {e}")
            raise RuntimeError(f"Error generating project with Cookiecutter: {e}") from e
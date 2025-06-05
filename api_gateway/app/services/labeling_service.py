from app.features.labeling_manager.labeling_manager import SuperbLabellingManager

def upload_images(project_name, team_name, superbai_token, image_path):
    manager = SuperbLabellingManager(project_name, team_name, superbai_token)
    manager.upload_images(image_path)
    
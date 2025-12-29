from pathlib import Path
from typing import cast
from ....framework import IController, DownloadableModel
from dataclasses import dataclass

@dataclass
class FasterWhisperModel(DownloadableModel):
    name: str

    def get_local_location(self, controller: IController) -> Path:
        return controller.resource_folder() / (self.name + '.pt')

    @classmethod
    def download(cls, models: list['DownloadableModel'], controller: IController):
        from .controller import FasterWhisperController
        controller = cast(FasterWhisperController, controller)
        instance_id = controller.run(None)
        api = controller.find_api(instance_id)
        for model in models:
            model = cast(FasterWhisperModel, model)
            api.load_model(model.name)
        controller.stop(instance_id)





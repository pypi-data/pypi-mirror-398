import json
from typing import Iterable
from unittest import TestCase

from ....framework import (
    File, RunConfiguration, TestReport, SmallImageBuilder, IImageBuilder,
    DockerWebServiceController, BrainBoxApi, BrainBoxTask, IModelDownloadingController, DownloadableModel
)
from .settings import FasterWhisperSettings, FasterWhisperModel
from pathlib import Path


class FasterWhisperController(DockerWebServiceController[FasterWhisperSettings], IModelDownloadingController):
    def get_image_builder(self) -> IImageBuilder|None:
        return SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            DEPENDENCIES.split('\n'),
        )

    def get_downloadable_model_type(self) -> type[DownloadableModel]:
        return FasterWhisperModel

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            None,
            publish_ports={self.connection_settings.port:8084},
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return FasterWhisperSettings()

    def create_api(self):
        from .api import FasterWhisper
        return FasterWhisper()

    def run_notebook(self):
        self.run_with_configuration(self.get_service_run_configuration(None).as_notebook_service())

    def post_install(self):
        self.download_models(self.settings.models_to_download)


    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import FasterWhisper

        file = File.read(Path(__file__).parent / 'files/test_voice.wav')

        first_time = True
        for model in self.settings.models_to_download:
            result = api.execute(BrainBoxTask.call(FasterWhisper).transcribe_json(file, model.name))
            yield TestReport.last_call(api).with_comment("Speech recognition with FasterWhisper, full output")
            tc.assertEqual(
                'One little spark and before you know it, the whole world is burning.',
                result['text'].strip()
            )

            result = api.execute(BrainBoxTask.call(FasterWhisper).transcribe(file, model.name))
            if first_time:
                yield TestReport.last_call(api).href('recognition').with_comment("Speech recognition with FasterWhisper, text-only output")
            tc.assertEqual(
                'One little spark and before you know it, the whole world is burning.',
                result
            )



DOCKERFILE=f'''
FROM python:3.9

{SmallImageBuilder.APT_INSTALL('ffmpeg')}

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

COPY . /home/app/

RUN pip freeze

ENTRYPOINT ["python3","/home/app/main.py"]

'''


DEPENDENCIES = '''
flask
notebook
faster-whisper
tqdm
ipywidgets
jupyter
hf_xet
'''

ORIGINAL_DEPENDENCIES='''
flask
notebook
faster-whisper
tqdm
ipywidgets
jupyter
hf_xet
'''
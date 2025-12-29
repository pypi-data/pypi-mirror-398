from brainbox.deciders.voice_analysis.faster_whisper import FasterWhisper

if __name__ == '__main__':
    controller = FasterWhisper.Controller()
    controller.install()
    controller.run_notebook()
    #controller.self_test()

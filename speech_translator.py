import azure.cognitiveservices.speech as speechsdk


class SpeechTranslator:
    def __init__(self, api_key, region='westeurope', source_language='de-DE', target_language='en'):
        self.api_key = api_key
        self.region = region
        self.source_language = source_language
        self.target_language = target_language
        self.done = False

    def stop_cb(self, evt):
        print('CLOSING on {}'.format(evt))
        self.done = True

    def recognized_cb(self, evt, speech_synthesizer):
        if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
            print('Recognized: {}'.format(evt.result.text))
            print('Translated into English: {}'.format(evt.result.translations[self.target_language]))

            ssml_text = """
            <speak version='1.0' xmlns='https://www.w3.org/2001/10/synthesis' xmlns:mstts='https://www.w3.org/2001/mstts' xml:lang='en-US'>
            <voice name='en-US-GuyNeural'>
            <mstts:express-as style='default'>
            {}
            </mstts:express-as>
            </voice>
            </speak>
            """.format(evt.result.translations[self.target_language])

            result_speech_synthesis = speech_synthesizer.speak_ssml_async(ssml_text).get()

            if result_speech_synthesis.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print('Speech synthesized for text [{}]'.format(result_speech_synthesis.text))
            elif result_speech_synthesis.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result_speech_synthesis.cancellation_details
                print('Speech synthesis canceled: {}'.format(cancellation_details.reason))
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    print('Error details: {}'.format(cancellation_details.error_details))

    def translate_speech(self):
        try:
            translation_config = speechsdk.translation.SpeechTranslationConfig(
                subscription=self.api_key, region=self.region)

            translation_config.speech_recognition_language = self.source_language
            translation_config.add_target_language(self.target_language)

            speech_config = speechsdk.SpeechConfig(subscription=self.api_key, region=self.region)
            speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

            recognizer = speechsdk.translation.TranslationRecognizer(translation_config=translation_config)

            recognizer.recognized.connect(lambda evt: self.recognized_cb(evt, speech_synthesizer))
            recognizer.session_stopped.connect(self.stop_cb)

            recognizer.start_continuous_recognition()

            while not self.done:
                pass

            recognizer.stop_continuous_recognition()

        except Exception as e:
            print(f"An error occurred: {e}")

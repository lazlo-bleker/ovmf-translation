import azure.cognitiveservices.speech as speechsdk


class SpeechTranslator:
    def __init__(self, api_key, region='westeurope', source_language='de-DE', target_language='en',
                 intermediate_translations=True, verbose=True):
        self.api_key = api_key
        self.region = region
        self.source_language = source_language
        self.target_language = target_language
        self.intermediate_translations = intermediate_translations
        self.verbose = verbose
        self.done = False
        self.last_synthesized_index = 0
        self.intermediate_buffer = ["", "", ""]
        self.synthesized_text = ""

    def log(self, message):
        if self.verbose:
            print(message)

    def stop_cb(self, evt):
        self.log(f'Translation stopped')
        self.done = True

    def recognized_cb(self, evt, speech_synthesizer):
        if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
            translation = evt.result.translations[self.target_language]
            if self.synthesized_text == translation[:len(self.synthesized_text)]:
                ok = 'OK'
            else:
                ok = 'ERROR'
            self.log(f'Final translation ({ok}): {translation}')
            text_to_synthesize = evt.result.translations[self.target_language][self.last_synthesized_index:]
            self.last_synthesized_index = 0
            self.synthesized_text = ""
            self.synthesize_text(text_to_synthesize, speech_synthesizer)

    def recognizing_cb(self, evt, speech_synthesizer):
        if evt.result.reason == speechsdk.ResultReason.TranslatingSpeech:
            self.intermediate_buffer.pop(0)
            self.intermediate_buffer.append(evt.result.translations[self.target_language])
            if all(". " in text for text in self.intermediate_buffer):
                up_to_dot = [text[:text.rindex(". ") + 1] for text in self.intermediate_buffer]
                if up_to_dot[0] == up_to_dot[1] == up_to_dot[2]:
                    text_to_synthesize = up_to_dot[0][self.last_synthesized_index:]
                    self.last_synthesized_index = len(up_to_dot[0])
                    if len(text_to_synthesize) > 0:
                        self.log(f'Intermediate translation: {text_to_synthesize}')
                        self.synthesized_text += text_to_synthesize
                        self.synthesize_text(text_to_synthesize, speech_synthesizer)

    def synthesize_text(self, text, speech_synthesizer):
        ssml_text = """
            <speak version='1.0' xmlns='https://www.w3.org/2001/10/synthesis' xmlns:mstts='https://www.w3.org/2001/mstts' xml:lang='en-US'>
            <voice name='en-US-GuyNeural'>
            <prosody rate='+30%'>
            <mstts:express-as style='default'>
            {}
            </mstts:express-as>
            </prosody>
            </voice>
            </speak>
            """.format(text)
        speech_synthesizer.speak_ssml_async(ssml_text)

    def translate_speech(self):
        translation_config = speechsdk.translation.SpeechTranslationConfig(
            subscription=self.api_key, region=self.region)

        speech_config = speechsdk.SpeechConfig(subscription=self.api_key, region=self.region)
        translation_config.speech_recognition_language = self.source_language
        translation_config.add_target_language(self.target_language)

        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        recognizer = speechsdk.translation.TranslationRecognizer(translation_config=translation_config)

        recognizer.session_stopped.connect(self.stop_cb)
        recognizer.recognized.connect(lambda evt: self.recognized_cb(evt, speech_synthesizer))
        if self.intermediate_translations:
            recognizer.recognizing.connect(lambda evt: self.recognizing_cb(evt, speech_synthesizer))

        recognizer.start_continuous_recognition()
        try:
            while not self.done:
                pass
        except KeyboardInterrupt:
            recognizer.stop_continuous_recognition()

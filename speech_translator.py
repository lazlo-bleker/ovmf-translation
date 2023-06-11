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
        self.done = False  # Will be used to signal when translation should stop
        self.last_synthesized_index = 0  # To keep track of the last index of the last synthesized text
        self.intermediate_buffer = ["", "", ""]  # Buffer for storing the 3 most recent intermediate translations
        self.synthesized_text = ""  # Stores cumulative intermediate translations

    def log(self, message):
        if self.verbose:
            print(message)

    # Callback function for when the translation session stops
    def stop_cb(self, evt):
        self.log('Translation stopped')
        self.done = True  # Sets done to True, signaling the translation to stop

    # Callback function for when a phrase has been fully recognized and translated
    def recognized_cb(self, evt, speech_synthesizer):
        # Check if the reason for the event is translated speech
        if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
            translation = evt.result.translations[self.target_language]
            # Compare cumulative intermediate translations with the final translation
            if self.synthesized_text == translation[:len(self.synthesized_text)]:
                ok = 'OK'
            else:
                ok = 'ERROR'
            self.log(f'Final translation ({ok}): {translation}')
            text_to_synthesize = evt.result.translations[self.target_language][self.last_synthesized_index:]
            self.last_synthesized_index = 0  # Reset the last synthesized text index
            self.synthesized_text = ""  # Reset cumulative intermediate translations
            self.synthesize_text(text_to_synthesize, speech_synthesizer)  # Synthesize the translated text

    # Callback function for when speech is being recognized and translated
    def recognizing_cb(self, evt, speech_synthesizer):
        # Check if the reason for the event is translating speech
        if evt.result.reason == speechsdk.ResultReason.TranslatingSpeech:
            # Update the intermediate translation buffer with the latest translation
            self.intermediate_buffer.pop(0)
            self.intermediate_buffer.append(evt.result.translations[self.target_language])
            # If all buffer entries contain ". ", proceed with equality check
            if all(". " in text for text in self.intermediate_buffer):
                up_to_dot = [text[:text.rindex(". ") + 1] for text in self.intermediate_buffer]
                # If all buffer entries are the same up to the last ". ", proceed with synthesis
                if up_to_dot[0] == up_to_dot[1] == up_to_dot[2]:
                    text_to_synthesize = up_to_dot[0][self.last_synthesized_index:]
                    self.last_synthesized_index = len(up_to_dot[0])  # Update the last synthesized text index
                    # If there is text to synthesize, log it and synthesize it
                    if len(text_to_synthesize) > 0:
                        self.log(f'Intermediate translation: {text_to_synthesize}')
                        self.synthesized_text += text_to_synthesize  # Update the until now synthesized text
                        self.synthesize_text(text_to_synthesize, speech_synthesizer)

    # Function to synthesize text into speech
    def synthesize_text(self, text, speech_synthesizer):
        # Define the SSML text for the speech synthesizer
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
        speech_synthesizer.speak_ssml_async(ssml_text)  # Pass the SSML text to the speech synthesizer

    # Main function to initiate and control the speech translation process
    def translate_speech(self):
        # Create configuration for translation
        translation_config = speechsdk.translation.SpeechTranslationConfig(
            subscription=self.api_key, region=self.region)
        # Create configuration for speech
        speech_config = speechsdk.SpeechConfig(subscription=self.api_key, region=self.region)
        translation_config.speech_recognition_language = self.source_language
        translation_config.add_target_language(self.target_language)

        # Create a speech synthesizer and a translation recognizer
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        recognizer = speechsdk.translation.TranslationRecognizer(translation_config=translation_config)

        # Connect callback functions to the appropriate events
        recognizer.session_stopped.connect(self.stop_cb)
        recognizer.recognized.connect(lambda evt: self.recognized_cb(evt, speech_synthesizer))
        if self.intermediate_translations:
            recognizer.recognizing.connect(lambda evt: self.recognizing_cb(evt, speech_synthesizer))

        recognizer.start_continuous_recognition()  # Start continuous recognition
        # Run a loop to keep the program running until translation is interrupted
        try:
            while not self.done:
                pass
        except KeyboardInterrupt:
            recognizer.stop_continuous_recognition()

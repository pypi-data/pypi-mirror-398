import os
from fabriq.document_loader import DocumentLoader
from fabriq.llm import LLM
from fabriq.wardrobe import TextSummarization
import cv2
from langchain_core.documents import Document
import asyncio


class VideoAnalysisLoader:
    def __init__(self, config):
        self.config = config
        self._doc_loader = DocumentLoader(config)
        self._llm = LLM(config)

    def check_runtime(self):
        try:
            from IPython import get_ipython

            shell = get_ipython().__class__.__name__
            if shell == "ZMQInteractiveShell":
                return "jupyter"
            elif shell == "TerminalInteractiveShell":
                return "terminal"
            else:
                return "other"
        except NameError:
            return "script"

    def _extract_frames(self, video_path: str = None):
        if video_path is None:
            raise ValueError("Video path must be provided")
        cap = cv2.VideoCapture(video_path)
        frames = []
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        cv2.destroyAllWindows()
        return frames

    def load(self, video_path: str = None, summarize: bool = True, metadata: dict = {}):
        # frames = self._extract_frames(video_path)
        audio_document = self._doc_loader.load_document(
            file_path=video_path, llm=self._llm
        )
        audio_text = audio_document[0].page_content.strip() if audio_document else ""
        audio_metadata = audio_document[0].metadata if audio_document else {}
        metadata.update(audio_metadata)
        print(metadata)

        if audio_text == "":
            raise ValueError("Fabriq Says: No audio transcript found in the video. Please check the video.")

        # if len(frames) > 0:
        #     if self.check_runtime() == "jupyter":
        #         import nest_asyncio

        #         nest_asyncio.apply()
        #     frame_descriptions = asyncio.run(
        #         self._llm.generate_batch_async(
        #             prompts=["Describe the content of this image in detail."]
        #             * len(frames),
        #             images=frames,
        #         )
        #     )

        #     combined_description = (
        #         "\n".join(frame_descriptions) + "\n\nAudio Transcript:\n" + audio_text
        #     )
        # else:
        combined_description = "Audio Transcript:\n" + audio_text

        if summarize:
            summary_prompt = (
                """Given the following content from a video, Summarize the following content in a concise manner.
                If there are any notable objects, people, or events, please include them in the summary.\n\n
                Text:
                {text}"""
            )
            summarizer = TextSummarization(self._llm, summary_prompt)
            summary = summarizer.summarize_text(text=combined_description)
            metadata.update({"summary": summary})

        return [
            Document(
                page_content=combined_description,
                metadata={
                    "source": video_path,
                    "file_name": os.path.basename(video_path) if video_path else None,
                    **metadata,
                },
            )
        ]

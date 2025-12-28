from automation_error_detector.application.dto.screen_result_dto import ScreenResultDTO
from automation_error_detector.domain.services.ai_service import AIService
from automation_error_detector.domain.value_objects.screen_text import ScreenText
from automation_error_detector.domain.value_objects.keywords import Keywords
from automation_error_detector.domain.services.signature_service import SignatureService
from automation_error_detector.shared.normalization import extract_keywords
from automation_error_detector.domain.services.cache_callback import CacheSaveCallback


class DetectScreenUseCase:
    def __init__(
        self,
        cache_callback: CacheSaveCallback,
        ai_client: AIService,
    ):
        self.cache_callback = cache_callback
        self.ai_client = ai_client

    def execute(self, raw_text: str) -> ScreenResultDTO:
        screen_text = ScreenText(raw_text)

        keywords_list = extract_keywords(screen_text.raw_text)
        keywords = Keywords(keywords_list)

        # 🔹 signature RIÊNG cho screen detection
        signature = SignatureService.generate(
            keywords=keywords,
            purpose="SCREEN",
        )

        cached = self.cache_callback.load(signature)
        if cached:
            return ScreenResultDTO(
                screen_type=cached["screen_type"],
                confidence=cached["confidence"],
                keywords=cached["keywords"],
                reason=cached["reason"],
                source="CACHE",
            )

        ai_result = self.ai_client.detect_screen(screen_text.raw_text)

        # 🔥 CALLBACK SAVE
        self.cache_callback.save(signature, ai_result)

        return ScreenResultDTO(
            screen_type=ai_result["screen_type"],
            confidence=ai_result["confidence"],
            keywords=ai_result["keywords"],
            reason=ai_result["reason"],
            source="AI",
        )

    # =========================
    # ASYNC
    # =========================
    async def aexecute(self, raw_text: str) -> ScreenResultDTO:
        screen_text = ScreenText(raw_text)

        keywords = Keywords(extract_keywords(screen_text.raw_text))
        signature = SignatureService.generate(
            keywords=keywords,
            purpose="SCREEN",
        )

        cached = await self.cache_callback.aload(signature)
        if cached:
            return ScreenResultDTO(
                screen_type=cached["screen_type"],
                confidence=cached["confidence"],
                keywords=cached["keywords"],
                reason=cached["reason"],
                source="CACHE",
            )

        ai_result = await self.ai_client.adetect_screen(screen_text.raw_text)

        await self.cache_callback.asave(signature, ai_result)

        return ScreenResultDTO(
            screen_type=ai_result["screen_type"],
            confidence=ai_result["confidence"],
            keywords=ai_result["keywords"],
            reason=ai_result["reason"],
            source="AI",
        )

"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Tests for long text chunking with multiple languages, abbreviations,
and mixed scripts (Cyrillic/Latin).
"""

import asyncio
from pathlib import Path

import pytest

from svo_client import ChunkerClient


@pytest.mark.asyncio
class TestLongTextMultiLang:
    """Tests for long text chunking with multiple languages."""

    @pytest.fixture
    def mtls_certs(self):
        """Get mTLS certificate paths."""
        cert_dir = Path("mtls_certificates")
        if not cert_dir.exists():
            pytest.skip("mTLS certificates not found")

        cert = cert_dir / "client" / "svo-chunker.crt"
        key = cert_dir / "client" / "svo-chunker.key"
        ca = cert_dir / "ca" / "ca.crt"

        if not (cert.exists() and key.exists() and ca.exists()):
            pytest.skip("mTLS certificates incomplete")

        return {
            "cert": str(cert),
            "key": str(key),
            "ca": str(ca),
        }

    # Use server_available from conftest

    async def test_long_text_russian(self, server_available, mtls_certs):
        """Test long Russian text with Cyrillic abbreviations."""
        if not server_available:
            pytest.fail("Server not available on localhost:8009")

        text = """
        Штучний інтелект (AI) - це галузь комп'ютерних наук, яка займається створенням інтелектуальних машин.
        Машинне навчання (ML) є підмножиною AI, яка дозволяє системам автоматично вчитися та покращуватися з досвіду.
        Глибоке навчання (DL) використовує нейронні мережі для моделювання та розуміння складних патернів.
        Природна обробка мови (NLP) дозволяє комп'ютерам розуміти, інтерпретувати та генерувати людську мову.
        Комп'ютерний зір (CV) дозволяє машинам інтерпретувати та розуміти візуальну інформацію з навколишнього світу.
        Робототехніка (Robotics) поєднує AI, механіку та електроніку для створення автономних систем.
        Експертні системи (ES) використовують знання та логічні правила для вирішення проблем у конкретних областях.
        Обробка великих даних (Big Data) вимагає AI для аналізу та виявлення корисних інсайтів.
        Кібербезпека (Cybersecurity) використовує AI для виявлення та запобігання кібератакам.
        Автономні транспортні засоби (AV) використовують AI для навігації та прийняття рішень у реальному часі.
        """ * 3

        # Test server runs on HTTP
        async with ChunkerClient(
            host="localhost",
            port=8009,
            timeout=120.0,
        ) as client:
            chunks = await client.chunk_text(
                text.strip(), type="Draft", language="uk"
            )
            assert len(chunks) > 0

            # Verify integrity
            reconstructed = client.reconstruct_text(chunks)
            assert reconstructed == text.strip()

    async def test_long_text_ukrainian(self, server_available, mtls_certs):
        """Test long Ukrainian text with mixed abbreviations."""
        if not server_available:
            pytest.fail("Server not available on localhost:8009")

        text = """
        Штучний інтелект (AI) - це галузь комп'ютерних наук, яка займається створенням інтелектуальних машин.
        Машинне навчання (ML) є підмножиною AI, яка дозволяє системам автоматично вчитися та покращуватися з досвіду.
        Глибоке навчання (DL) використовує нейронні мережі для моделювання та розуміння складних патернів.
        Природна обробка мови (NLP) дозволяє комп'ютерам розуміти, інтерпретувати та генерувати людську мову.
        Комп'ютерний зір (CV) дозволяє машинам інтерпретувати та розуміти візуальну інформацію з навколишнього світу.
        Робототехніка (Robotics) поєднує AI, механіку та електроніку для створення автономних систем.
        Експертні системи (ES) використовують знання та логічні правила для вирішення проблем у конкретних областях.
        Обробка великих даних (Big Data) вимагає AI для аналізу та виявлення корисних інсайтів.
        Кібербезпека (Cybersecurity) використовує AI для виявлення та запобігання кібератакам.
        Автономні транспортні засоби (AV) використовують AI для навігації та прийняття рішень у реальному часі.
        """ * 3

        # Test server runs on HTTP
        async with ChunkerClient(
            host="localhost",
            port=8009,
            timeout=120.0,
        ) as client:
            chunks = await client.chunk_text(
                text.strip(), type="Draft", language="uk"
            )
            assert len(chunks) > 0

            # Verify integrity
            reconstructed = client.reconstruct_text(chunks)
            assert reconstructed == text.strip()

    async def test_long_text_english(self, server_available, mtls_certs):
        """Test long English text with abbreviations."""
        if not server_available:
            pytest.fail("Server not available on localhost:8009")

        text = """
        Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines.
        Machine Learning (ML) is a subset of AI that enables systems to automatically learn and improve from experience.
        Deep Learning (DL) uses neural networks to model and understand complex patterns.
        Natural Language Processing (NLP) enables computers to understand, interpret, and generate human language.
        Computer Vision (CV) enables machines to interpret and understand visual information from the world.
        Robotics combines AI, mechanics, and electronics to create autonomous systems.
        Expert Systems (ES) use knowledge and logical rules to solve problems in specific domains.
        Big Data processing requires AI for analysis and discovering useful insights.
        Cybersecurity uses AI to detect and prevent cyberattacks.
        Autonomous Vehicles (AV) use AI for navigation and decision-making in real-time.
        """ * 3

        # Test server runs on HTTP
        async with ChunkerClient(
            host="localhost",
            port=8009,
            timeout=120.0,
        ) as client:
            chunks = await client.chunk_text(
                text.strip(), type="Draft", language="en"
            )
            assert len(chunks) > 0

            # Verify integrity
            reconstructed = client.reconstruct_text(chunks)
            assert reconstructed == text.strip()

    async def test_mixed_scripts_cyrillic_latin(self, server_available, mtls_certs):
        """Test text with mixed Cyrillic and Latin scripts."""
        if not server_available:
            pytest.fail("Server not available on localhost:8009")

        text = """
        Штучний інтелект (AI) використовує машинне навчання (ML) для обробки даних.
        Deep Learning (DL) дозволяє системам автоматично вчитися з прикладів.
        Natural Language Processing (NLP) обробляє текст українською та англійською мовами.
        Комп'ютерний зір (CV) розпізнає об'єкти на зображеннях та відео.
        Big Data аналізує великі обсяги інформації для виявлення патернів.
        Cybersecurity захищає системи від кібератак та витоків даних.
        Автономні транспортні засоби (AV) використовують AI для навігації.
        Експертні системи (ES) допомагають приймати рішення в складних ситуаціях.
        Робототехніка (Robotics) поєднує AI з механікою для створення автономних роботів.
        Обробка великих даних вимагає потужних обчислювальних ресурсів та AI алгоритмів.
        """ * 3

        # Test server runs on HTTP
        async with ChunkerClient(
            host="localhost",
            port=8009,
            timeout=120.0,
        ) as client:
            chunks = await client.chunk_text(
                text.strip(), type="Draft", language="uk"
            )
            assert len(chunks) > 0

            # Verify integrity
            reconstructed = client.reconstruct_text(chunks)
            assert reconstructed == text.strip()

    async def test_mixed_abbreviations(self, server_available, mtls_certs):
        """Test text with mixed Cyrillic and Latin abbreviations."""
        if not server_available:
            pytest.fail("Server not available on localhost:8009")

        text = """
        AI (Artificial Intelligence) та ШІ (Штучний Інтелект) - це одне й те саме.
        ML (Machine Learning) та МН (Машинне Навчання) використовують алгоритми для навчання.
        DL (Deep Learning) та ГН (Глибоке Навчання) базуються на нейронних мережах.
        NLP (Natural Language Processing) та ОМ (Обробка Мови) працюють з текстом.
        CV (Computer Vision) та КЗ (Комп'ютерний Зір) аналізують візуальну інформацію.
        Big Data та Великі Дані потребують потужних обчислювальних систем.
        Cybersecurity та Кібербезпека захищають інформаційні системи.
        AV (Autonomous Vehicles) та АТЗ (Автономні Транспортні Засоби) використовують AI.
        ES (Expert Systems) та ЕС (Експертні Системи) допомагають приймати рішення.
        Robotics та Робототехніка створюють автономні механічні системи.
        """ * 3

        # Test server runs on HTTP
        async with ChunkerClient(
            host="localhost",
            port=8009,
            timeout=120.0,
        ) as client:
            chunks = await client.chunk_text(
                text.strip(), type="Draft", language="uk"
            )
            assert len(chunks) > 0

            # Verify integrity
            reconstructed = client.reconstruct_text(chunks)
            assert reconstructed == text.strip()

    async def test_latin_in_cyrillic(self, server_available, mtls_certs):
        """Test text with Latin words embedded in Cyrillic text."""
        if not server_available:
            pytest.fail("Server not available on localhost:8009")

        text = """
        Штучний інтелект використовує machine learning для обробки даних.
        Deep learning дозволяє системам автоматично вчитися з прикладів.
        Natural language processing обробляє текст українською мовою.
        Computer vision розпізнає об'єкти на зображеннях та відео.
        Big data аналізує великі обсяги інформації для виявлення патернів.
        Cybersecurity захищає системи від кібератак та витоків даних.
        Autonomous vehicles використовують AI для навігації по дорогах.
        Expert systems допомагають приймати рішення в складних ситуаціях.
        Robotics поєднує AI з механікою для створення автономних роботів.
        Data processing вимагає потужних обчислювальних ресурсів та алгоритмів.
        """ * 3

        # Test server runs on HTTP
        async with ChunkerClient(
            host="localhost",
            port=8009,
            timeout=120.0,
        ) as client:
            chunks = await client.chunk_text(
                text.strip(), type="Draft", language="uk"
            )
            assert len(chunks) > 0

            # Verify integrity
            reconstructed = client.reconstruct_text(chunks)
            assert reconstructed == text.strip()

    async def test_cyrillic_in_latin(self, server_available, mtls_certs):
        """Test text with Cyrillic words embedded in Latin text."""
        if not server_available:
            pytest.fail("Server not available on localhost:8009")

        text = """
        Artificial Intelligence використовує машинне навчання для обробки даних.
        Machine Learning дозволяє системам автоматично вчитися з прикладів.
        Natural Language Processing обробляє текст українською та англійською мовами.
        Computer Vision розпізнає об'єкти на зображеннях та відео.
        Big Data аналізує великі обсяги інформації для виявлення патернів.
        Cybersecurity захищає системи від кібератак та витоків даних.
        Autonomous Vehicles використовують AI для навігації по дорогах.
        Expert Systems допомагають приймати рішення в складних ситуаціях.
        Robotics поєднує AI з механікою для створення автономних роботів.
        Data Processing вимагає потужних обчислювальних ресурсів та алгоритмів.
        """ * 3

        # Test server runs on HTTP
        async with ChunkerClient(
            host="localhost",
            port=8009,
            timeout=120.0,
        ) as client:
            chunks = await client.chunk_text(
                text.strip(), type="Draft", language="en"
            )
            assert len(chunks) > 0

            # Verify integrity
            reconstructed = client.reconstruct_text(chunks)
            assert reconstructed == text.strip()


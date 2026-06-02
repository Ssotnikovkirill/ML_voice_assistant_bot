import whisper
from transformers import GPT2LMHeadModel, GPT2Tokenizer

import smtplib
import ssl
from email.mime.text import MIMEText

model_name = 'sberbank-ai/rugpt2large'
gpt2_tokenizer = GPT2Tokenizer.from_pretrained(model_name)
gpt2_model = GPT2LMHeadModel.from_pretrained(model_name)
gpt2_model.eval()


whisper_model = whisper.load_model("small")

def transcribe_audio(audio_path):
    result = whisper_model.transcribe(audio_path, language='ru')
    return result['text']


# def generate_direct_command(text):
#     prompt = f"""Перефразируй, но не выдумывай не сказанного, в прямое деловое сообщение с обращением без дополнительных приписок (только имя + глагол в повелительном наклонении в будущем времени), только то что указано:
# Пример исходного: "Сообщи Данилу Петрову, что он должен занести документы об образовании"
# Результат: "Данил Петров, занесите документы об образовании"

# Исходное: "{text}"
# Результат:"""

#     inputs = gpt2_tokenizer(prompt, return_tensors="pt")
#     outputs = gpt2_model.generate(
#         inputs.input_ids,
#         max_new_tokens=30,
#         num_beams=5,
#         no_repeat_ngram_size=2,
#         temperature=0.1,
#         pad_token_id=gpt2_tokenizer.eos_token_id,
#         early_stopping=True
#     )

#     decoded = gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
#     result = decoded.split("Результат:")[-1].strip(' "\n')
#     # Чистим лишнее
#     result = result.split('"')[0].split("Исход")[0].strip()
#     return result

def generate_direct_command(text):
    prompt = f"""
Ты помощник-ассистент. Преобразуй только суть команды, строго. 
Говори от имени руководителя, используя только обращение по имени и глагол в повелительном наклонении. Не добавляй ничего выдуманного.

Пример:
Исходное: Сообщи Данилу Петрову, что он должен занести документы об образовании
Результат: Данил Петров, занесите документы об образовании

Исходное: {text}
Результат:"""

    inputs = gpt2_tokenizer(prompt, return_tensors="pt")
    outputs = gpt2_model.generate(
        inputs.input_ids,
        max_new_tokens=25,
        num_beams=5,
        no_repeat_ngram_size=3,
        temperature=0.9,
        repetition_penalty=1.1,
        pad_token_id=gpt2_tokenizer.eos_token_id,
        early_stopping=True
    )

    decoded = gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
    result = decoded.split("Результат:")[-1].strip(' "\n')
    result = result.split("\n")[0].split('"')[0].split("Исход")[0].strip()
    return result



def send_gmail(sender, password, recipient, subject, body):
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())

        return True
    except Exception as e:
        print(f"Ошибка отправки Email: {str(e)}")
        return False

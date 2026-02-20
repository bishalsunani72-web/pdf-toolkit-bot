import os
import fitz
import zipfile
from docx import Document
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler, CallbackContext

BOT_TOKEN = os.getenv("BOT_TOKEN")

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Send me a PDF file to convert 😎")

def handle_pdf(update: Update, context: CallbackContext):
    file = update.message.document

    if not file.file_name.endswith(".pdf"):
        update.message.reply_text("Please send a PDF file.")
        return

    file_obj = file.get_file()
    file_obj.download("input.pdf")

    keyboard = [
        [InlineKeyboardButton("📷 All Images", callback_data="images")],
        [InlineKeyboardButton("🗜 Images ZIP", callback_data="zip")],
        [InlineKeyboardButton("👁 First Page Preview", callback_data="preview")],
        [InlineKeyboardButton("📄 Convert to Word", callback_data="word")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Choose conversion type:", reply_markup=reply_markup)

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    pdf = fitz.open("input.pdf")

    if query.data == "preview":
        page = pdf[0]
        pix = page.get_pixmap()
        pix.save("preview.png")
        query.message.reply_photo(open("preview.png", "rb"))
        os.remove("preview.png")

    elif query.data == "images":
        for i in range(len(pdf)):
            page = pdf[i]
            pix = page.get_pixmap()
            img_name = f"page_{i+1}.png"
            pix.save(img_name)
            query.message.reply_photo(open(img_name, "rb"))
            os.remove(img_name)

    elif query.data == "zip":
        zip_name = "images.zip"
        with zipfile.ZipFile(zip_name, "w") as zipf:
            for i in range(len(pdf)):
                page = pdf[i]
                pix = page.get_pixmap()
                img_name = f"page_{i+1}.png"
                pix.save(img_name)
                zipf.write(img_name)
                os.remove(img_name)

        query.message.reply_document(open(zip_name, "rb"))
        os.remove(zip_name)

    elif query.data == "word":
        doc = Document()
        for i in range(len(pdf)):
            page = pdf[i]
            text = page.get_text()
            doc.add_paragraph(text)

        doc.save("output.docx")
        query.message.reply_document(open("output.docx", "rb"))
        os.remove("output.docx")

    pdf.close()
    os.remove("input.pdf")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.document, handle_pdf))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.command, start))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

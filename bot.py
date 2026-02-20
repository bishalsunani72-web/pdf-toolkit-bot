import os
import fitz
import zipfile
from PIL import Image
from docx import Document
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler, CallbackContext, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")

user_images = {}

# High quality zoom factor
ZOOM = 2  # 2 = High quality | 3 = Very High (more memory use)

# START
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Welcome to PDF Toolkit Bot\n\n"
        "📄 Send PDF → Convert to Images / Word\n"
        "🖼 Send Images → Convert to PDF"
    )

# HANDLE PDF
def handle_pdf(update: Update, context: CallbackContext):
    file = update.message.document

    if not file.file_name.endswith(".pdf"):
        update.message.reply_text("❌ Please send a valid PDF file.")
        return

    file_obj = file.get_file()
    file_obj.download("input.pdf")

    keyboard = [
        [InlineKeyboardButton("📷 All Images (HD)", callback_data="images")],
        [InlineKeyboardButton("🗜 Images ZIP (HD)", callback_data="zip")],
        [InlineKeyboardButton("👁 First Page Preview (HD)", callback_data="preview")],
        [InlineKeyboardButton("📄 Convert to Word", callback_data="word")]
    ]

    update.message.reply_text(
        "Choose conversion type:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# HANDLE IMAGES
def handle_image(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]
    file = photo.get_file()

    if user_id not in user_images:
        user_images[user_id] = []

    file_path = f"{user_id}_{len(user_images[user_id])}.jpg"
    file.download(file_path)

    user_images[user_id].append(file_path)

    keyboard = [
        [InlineKeyboardButton("📄 Convert Images to PDF", callback_data="img2pdf")]
    ]

    update.message.reply_text(
        "✅ Image saved.\nSend more images or press convert.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# BUTTON HANDLER
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    # -------- PDF CONVERSIONS --------
    if os.path.exists("input.pdf"):
        pdf = fitz.open("input.pdf")

        if query.data in ["preview", "images", "zip"]:
            mat = fitz.Matrix(ZOOM, ZOOM)

        if query.data == "preview":
            page = pdf[0]
            pix = page.get_pixmap(matrix=mat)
            pix.save("preview.png")
            query.message.reply_photo(open("preview.png", "rb"))
            os.remove("preview.png")

        elif query.data == "images":
            for i in range(len(pdf)):
                page = pdf[i]
                pix = page.get_pixmap(matrix=mat)
                img_name = f"page_{i+1}.png"
                pix.save(img_name)
                query.message.reply_photo(open(img_name, "rb"))
                os.remove(img_name)

        elif query.data == "zip":
            zip_name = "images.zip"
            with zipfile.ZipFile(zip_name, "w") as zipf:
                for i in range(len(pdf)):
                    page = pdf[i]
                    pix = page.get_pixmap(matrix=mat)
                    img_name = f"page_{i+1}.png"
                    pix.save(img_name)
                    zipf.write(img_name)
                    os.remove(img_name)

            query.message.reply_document(open(zip_name, "rb"))
            os.remove(zip_name)

        elif query.data == "word":
            doc = Document()
            for i in range(len(pdf)):
                text = pdf[i].get_text()
                doc.add_paragraph(text)

            doc.save("output.docx")
            query.message.reply_document(open("output.docx", "rb"))
            os.remove("output.docx")

        pdf.close()
        os.remove("input.pdf")

    # -------- IMAGE TO PDF --------
    elif query.data == "img2pdf":
        user_id = query.from_user.id

        if user_id not in user_images or len(user_images[user_id]) == 0:
            query.message.reply_text("❌ No images found.")
            return

        image_list = []
        for img_path in user_images[user_id]:
            img = Image.open(img_path).convert("RGB")
            image_list.append(img)

        pdf_name = f"{user_id}_output.pdf"
        image_list[0].save(pdf_name, save_all=True, append_images=image_list[1:])

        query.message.reply_document(open(pdf_name, "rb"))

        for img_path in user_images[user_id]:
            os.remove(img_path)

        os.remove(pdf_name)
        user_images[user_id] = []

# MAIN
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_pdf))
    dp.add_handler(MessageHandler(Filters.photo, handle_image))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

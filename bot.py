import logging
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder,CommandHandler,MessageHandler,CallbackQueryHandler,filters,ContextTypes
from config import TOKEN,ADMIN_IDS
from database import init_db,cerca_numero,aggiungi_numero,segnala_spam,get_stats,get_pending,approva_numero,elimina_numero,get_all_numbers
import re
logging.basicConfig(level=logging.INFO)
def normalizza_numero(n):
    n=re.sub(r"[\s\-\(\)]","",n)
    if not n.startswith("+"):
        n="+39"+n
    return n
def is_numero_valido(n):
    return bool(re.match(r"^\+\d{7,15}$",n))
def is_admin(uid):
    return uid in ADMIN_IDS
async def start(u,c):
    await u.message.reply_text("👁 FoundIt Bot\n\n/cerca +39XXX\n/aggiungi +39XXX Nome\n/spam +39XXX\n/stats")
async def cmd_cerca(u,c):
    if not c.args:
        await u.message.reply_text("Uso: /cerca +39XXX"); return
    await _cerca(u,normalizza_numero(c.args[0]))
async def cmd_aggiungi(u,c):
    if len(c.args)<2:
        await u.message.reply_text("Uso: /aggiungi +39XXX Nome"); return
    n=normalizza_numero(c.args[0]); nome=" ".join(c.args[1:])
    if aggiungi_numero(n,nome,u.effective_user.id):
        await u.message.reply_text(f"✅ {n} = {nome} inviato per revisione!")
        for a in ADMIN_IDS:
            kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅",callback_data=f"approva:{n}"),InlineKeyboardButton("❌",callback_data=f"elimina:{n}")]])
            await c.bot.send_message(a,f"Nuovo: {n} = {nome}",reply_markup=kb)
    else:
        await u.message.reply_text("⚠️ Già presente.")
async def cmd_spam(u,c):
    if not c.args:
        await u.message.reply_text("Uso: /spam +39XXX"); return
    n=normalizza_numero(c.args[0]); score=segnala_spam(n,u.effective_user.id)
    await u.message.reply_text(f"🚨 Segnalato! Totale: {score}")
async def cmd_stats(u,c):
    s=get_stats()
    await u.message.reply_text(f"📊 Totale:{s['totale']} ✅:{s['approvati']} ⏳:{s['pending']} 🚨:{s['spam']}")
async def _cerca(u,numero):
    r=cerca_numero(numero)
    if r:
        spam="🚨 SPAM" if r['spam_score']>=3 else "✅"
        await u.message.reply_text(f"👤 {r['nome']}\n🚨 Spam:{r['spam_score']} {spam}\n📅 {r['data']}",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚨 Spam",callback_data=f"spam:{numero}")]]))
    else:
        await u.message.reply_text(f"❓ {numero} non trovato.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Aggiungi",callback_data=f"aggiungi:{numero}")]]))
async def gestisci(u,c):
    if "aggiungi_numero" in c.user_data:
        n=c.user_data.pop("aggiungi_numero"); nome=u.message.text.strip()
        aggiungi_numero(n,nome,u.effective_user.id)
        await u.message.reply_text(f"✅ {n}={nome} inviato!")
        for a in ADMIN_IDS:
            kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅",callback_data=f"approva:{n}"),InlineKeyboardButton("❌",callback_data=f"elimina:{n}")]])
            await c.bot.send_message(a,f"Nuovo: {n}={nome}",reply_markup=kb)
    else:
        n=normalizza_numero(u.message.text.strip())
        if is_numero_valido(n): await _cerca(u,n)
        else: await u.message.reply_text("❓ Inviami un numero o usa /start")
async def cb(u,c):
    q=u.callback_query; await q.answer(); d=q.data; uid=q.from_user.id
    if d.startswith("spam:"):
        score=segnala_spam(d.split(":",1)[1],uid); await q.message.reply_text(f"🚨 Segnalato! Totale:{score}")
    elif d.startswith("aggiungi:"):
        c.user_data["aggiungi_numero"]=d.split(":",1)[1]; await q.message.reply_text("Inviami il nome:")
    elif d.startswith("approva:") and is_admin(uid):
        approva_numero(d.split(":",1)[1]); await q.message.reply_text("✅ Approvato!")
    elif d.startswith("elimina:") and is_admin(uid):
        elimina_numero(d.split(":",1)[1]); await q.message.reply_text("🗑 Eliminato!")
async def cmd_pending(u,c):
    if not is_admin(u.effective_user.id): return
    for p in get_pending()[:10]:
        kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅",callback_data=f"approva:{p['numero']}"),InlineKeyboardButton("❌",callback_data=f"elimina:{p['numero']}")]])
        await u.message.reply_text(f"{p['numero']} = {p['nome']}",reply_markup=kb)
def main():
    init_db()
    app=ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("cerca",cmd_cerca))
    app.add_handler(CommandHandler("aggiungi",cmd_aggiungi))
    app.add_handler(CommandHandler("spam",cmd_spam))
    app.add_handler(CommandHandler("stats",cmd_stats))
    app.add_handler(CommandHandler("pending",cmd_pending))
    app.add_handler(CallbackQueryHandler(cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,gestisci))
    print("🤖 Avviato!"); app.run_polling()
if __name__=="__main__":
    main()

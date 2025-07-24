from flask import Flask, request, jsonify
from utility import translate_text, get_language_choice, list_languages

app = Flask(__name__)

FAQ_DATA = {
    "What is a mutual fund?": "A mutual fund is an investment vehicle made up of a pool of money collected from many investors to invest in stocks, bonds and other securities.",
    "What is meant by investment?": "Investment is the act of committing money or capital to an endeavor with the expectation of obtaining an additional income or profit.",
    "How do mutual funds work?": "Mutual funds collect money from investors and buy a diversified portfolio of assets managed by professional fund managers.",
    "What are the types of mutual funds?": "Types include equity funds, debt funds, balanced funds, index funds, among others.",
    "What are the risks associated with mutual funds?": "Risks include market risk, credit risk, interest rate risk, and others depending on the fund type.",
    "What are the benefits of investing in mutual funds?": "Mutual funds offer diversification, professional management, liquidity, and convenience for small investors.",
    "What is Systematic Investment Plan (SIP)?": "SIP is a method where you invest a fixed amount regularly in mutual funds, helping to average out market volatility.",
    "How is a mutual fund different from stocks?": "A mutual fund pools money to invest in many stocks or bonds, while buying stock means owning a part of a single company.",
    "What is the difference between equity and debt mutual funds?": "Equity funds invest mostly in stocks with higher growth and risk; debt funds invest in bonds with relatively lower risk and steady returns.",
    "What does NAV (Net Asset Value) mean?": "NAV is the per-unit price of a mutual fund, calculated daily, representing the market value of the fund’s assets minus liabilities.",
    "Are mutual funds safe investments?": "Mutual funds carry market risks, but diversification and professional management help reduce risk; always invest as per your risk profile.",
    "What is the lock-in period in mutual funds?": "Some funds, like ELSS (tax-saving mutual funds), have a minimum period you must hold before you can redeem without penalties.",
    "How does inflation affect my investments?": "Inflation reduces the value of money over time, so investments ideally should earn returns above inflation to grow your real wealth.",
    "What tax benefits do mutual funds offer?": "Some funds provide tax deductions or lower tax rates on returns, especially ELSS and long-term capital gains from equity funds.",
    "Can I redeem my mutual fund units anytime?": "Most funds allow you to redeem units anytime, but some schemes have exit loads or lock-in periods restricting early withdrawal."
}

TRANSLATE_PROJECT_ID = "gmail-automation-463517"  # your GCP project id


@app.route('/faq/questions', methods=['POST'])
def get_faq_questions():
    """
    Request JSON:
    {
        "preferred_language": "en"  # language code, e.g. 'hi', 'ta', etc.
    }
    Response JSON:
    {
        "questions": ["Question1", "Question2", ...]  // translated if needed
    }
    """
    data = request.json or {}
    preferred_language = data.get("preferred_language", "en")

    questions = list(FAQ_DATA.keys())
    if preferred_language != 'en':
        try:
            questions_translated = [translate_text(q, preferred_language, TRANSLATE_PROJECT_ID) for q in questions]
        except Exception as e:
            # If translation fails, fallback to English questions
            print(f"Translation error in questions: {e}")
            questions_translated = questions
    else:
        questions_translated = questions

    return jsonify({"questions": questions_translated})


@app.route('/faq/answer', methods=['POST'])
def get_faq_answer():
    """
    Request JSON:
    {
        "preferred_language": "en",
        "question_index": 0     # index of the question selected from /faq/questions
    }
    OR
    {
        "preferred_language": "en",
        "question_text": "What is a mutual fund?"   # exact question text in English or translated (optional)
    }
    Response JSON:
    {
        "answer": "Answer text"  // translated if needed
    }
    """
    data = request.json or {}
    preferred_language = data.get("preferred_language", "en")
    question_index = data.get("question_index", None)
    question_text = data.get("question_text", None)

    questions = list(FAQ_DATA.keys())

    # Determine question
    if question_text:
        # Try to match question_text with English keys by translation if needed
        if preferred_language != 'en':
            # To handle translated question text, try to find original by reverse translation
            # (Assuming translated question_text is sent, this is complicated and would require translation API call)
            # For simplicity, here we assume question_text is English or exact key.
            # You can improve this by mapping translated to original questions on /faq/questions call.
            pass

        if question_text in FAQ_DATA:
            key = question_text
        else:
            return jsonify({"error": "Question text not recognized"}), 400

    elif question_index is not None:
        if 0 <= question_index < len(questions):
            key = questions[question_index]
        else:
            return jsonify({"error": "Invalid question index"}), 400
    else:
        return jsonify({"error": "Must provide question_index or question_text"}), 400

    answer = FAQ_DATA[key]

    # Translate answer if needed
    if preferred_language != 'en':
        try:
            answer_translated = translate_text(answer, preferred_language, TRANSLATE_PROJECT_ID)
        except Exception as e:
            print(f"Translation error in answer: {e}")
            answer_translated = answer
    else:
        answer_translated = answer

    return jsonify({"answer": answer_translated})


if __name__ == "__main__":
    app.run(debug=True)

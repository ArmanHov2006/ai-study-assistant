"""
Study Tools Page - Summarize and Quiz Features
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import get_documents, summarize_document, generate_quiz

# Page configuration
st.set_page_config(
    page_title="Study Tools",
    page_icon="📚",
    layout="wide"
)

# Initialize session state for quiz
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = None

if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = {}

if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False

st.title("📚 Study Tools")
st.markdown("Generate summaries and quizzes to enhance your learning")

# Create tabs
tab1, tab2 = st.tabs(["📝 Summarize", "🎯 Quiz"])

# ============================================================================
# TAB 1: SUMMARIZE
# ============================================================================

with tab1:
    st.header("📝 Document Summary")
    st.markdown("Generate a comprehensive summary of your document")

    # Get documents
    docs_result = get_documents()

    if not docs_result["success"]:
        st.error(f"Failed to load documents: {docs_result['error']}")
    else:
        documents = docs_result["data"].get("documents", [])

        if not documents:
            st.info("📭 No documents available. Please upload documents first.")
        else:
            # Document selector
            doc_names = [doc["filename"] for doc in documents]
            selected_doc = st.selectbox(
                "Select a document to summarize:",
                options=doc_names,
                help="Choose a document to generate a summary"
            )

            # Generate summary button
            if st.button("Generate Summary", type="primary", key="summarize_btn"):
                with st.spinner(f"Generating summary for {selected_doc}..."):
                    result = summarize_document(selected_doc)

                    if result["success"]:
                        data = result["data"]

                        # Display summary
                        st.success("✅ Summary generated successfully!")

                        # Show metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Original Length", f"{data.get('original_length', 0):,} chars")
                        with col2:
                            st.metric("Summary Length", f"{data.get('summarized_length', 0):,} chars")
                        with col3:
                            st.metric("Compression Ratio", data.get('compression_ratio', 'N/A'))

                        st.markdown("---")

                        # Display the summary
                        st.markdown("### Summary")
                        st.markdown(data.get('summary', 'No summary available'))

                    else:
                        st.error(f"❌ Summarization failed: {result['error']}")

    # Tips
    with st.expander("💡 Summarization Tips", expanded=False):
        st.markdown("""
        ### How It Works
        - The AI analyzes your document and extracts key information
        - Summaries are structured with main topics, key points, and important details
        - Large documents (>50,000 characters) are automatically truncated

        ### Best For
        - Quick review of document content
        - Identifying main topics and themes
        - Preparing for deeper study
        - Getting an overview before reading the full document

        ### Tips
        - Summaries are most effective for well-structured documents
        - The compression ratio shows how much the content was condensed
        - Review the summary first, then read the full document for details
        """)

# ============================================================================
# TAB 2: QUIZ
# ============================================================================

with tab2:
    st.header("🎯 Interactive Quiz")
    st.markdown("Test your knowledge with AI-generated quizzes")

    # Get documents
    docs_result = get_documents()

    if not docs_result["success"]:
        st.error(f"Failed to load documents: {docs_result['error']}")
    else:
        documents = docs_result["data"].get("documents", [])

        if not documents:
            st.info("📭 No documents available. Please upload documents first.")
        else:
            # Quiz configuration section
            if not st.session_state.quiz_data or not st.session_state.quiz_submitted:
                st.subheader("Quiz Configuration")

                # Document mode selection
                quiz_mode = st.radio(
                    "Document Selection:",
                    options=["Single Document", "All Documents"],
                    help="Choose to quiz from one document or all uploaded documents"
                )

                # Document selector for single document mode
                selected_quiz_doc = None
                use_all_docs = False

                if quiz_mode == "Single Document":
                    doc_names = [doc["filename"] for doc in documents]
                    selected_quiz_doc = st.selectbox(
                        "Select document:",
                        options=doc_names,
                        help="Choose a document for the quiz"
                    )
                else:
                    use_all_docs = True
                    st.info(f"Quiz will be generated from all {len(documents)} document(s)")

                # Quiz parameters
                col1, col2 = st.columns(2)

                with col1:
                    num_questions = st.slider(
                        "Number of Questions:",
                        min_value=5,
                        max_value=40,
                        value=10,
                        step=1,
                        help="Select how many questions to generate"
                    )

                with col2:
                    difficulty = st.select_slider(
                        "Difficulty Level:",
                        options=["easy", "medium", "hard"],
                        value="medium",
                        help="Easy: basic recall | Medium: understanding | Hard: analysis"
                    )

                # Generate quiz button
                if st.button("Generate Quiz", type="primary", key="generate_quiz_btn"):
                    with st.spinner(f"Generating {num_questions} questions..."):
                        result = generate_quiz(
                            num_questions=num_questions,
                            difficulty=difficulty,
                            document_name=selected_quiz_doc,
                            use_all_documents=use_all_docs
                        )

                        if result["success"]:
                            st.session_state.quiz_data = result["data"]
                            st.session_state.quiz_answers = {}
                            st.session_state.quiz_submitted = False
                            st.success(f"✅ Generated {len(result['data']['questions'])} questions!")
                            st.rerun()
                        else:
                            st.error(f"❌ Quiz generation failed: {result['error']}")

            # Display quiz questions
            if st.session_state.quiz_data and not st.session_state.quiz_submitted:
                st.markdown("---")
                st.subheader("Answer the Questions")

                questions = st.session_state.quiz_data.get("questions", [])

                for idx, question in enumerate(questions):
                    st.markdown(f"### Question {idx + 1} of {len(questions)}")

                    q_type = question.get("type")
                    q_text = question.get("question")

                    st.markdown(f"**{q_text}**")

                    if q_type == "multiple_choice":
                        # Multiple choice question
                        options = question.get("options", {})
                        option_labels = [f"{key}: {value}" for key, value in options.items()]

                        answer = st.radio(
                            "Select your answer:",
                            options=list(options.keys()),
                            format_func=lambda x: f"{x}: {options[x]}",
                            key=f"q_{idx}",
                            index=None
                        )

                        st.session_state.quiz_answers[idx] = {
                            "type": "multiple_choice",
                            "answer": answer,
                            "correct": question.get("correct")
                        }

                    elif q_type == "short_answer":
                        # Short answer question
                        answer = st.text_area(
                            "Your answer:",
                            key=f"q_{idx}",
                            height=100,
                            placeholder="Type your answer here..."
                        )

                        st.session_state.quiz_answers[idx] = {
                            "type": "short_answer",
                            "answer": answer,
                            "correct_answer": question.get("correct_answer", ""),
                            "acceptable_variations": question.get("acceptable_variations", [])
                        }

                    st.markdown("---")

                # Submit button
                if st.button("Submit Answers", type="primary", key="submit_quiz_btn"):
                    # Check if all questions are answered
                    all_answered = all(
                        st.session_state.quiz_answers.get(i, {}).get("answer")
                        for i in range(len(questions))
                    )

                    if not all_answered:
                        st.warning("⚠️ Please answer all questions before submitting.")
                    else:
                        st.session_state.quiz_submitted = True
                        st.rerun()

            # Display quiz results
            if st.session_state.quiz_data and st.session_state.quiz_submitted:
                st.markdown("---")
                st.subheader("📊 Quiz Results")

                questions = st.session_state.quiz_data.get("questions", [])
                correct_count = 0
                total_questions = len(questions)

                # Calculate score
                for idx, question in enumerate(questions):
                    user_answer_data = st.session_state.quiz_answers.get(idx, {})
                    user_answer = user_answer_data.get("answer", "")

                    if question["type"] == "multiple_choice":
                        correct_answer = question.get("correct")
                        is_correct = user_answer == correct_answer
                    else:  # short_answer
                        correct_answer = question.get("correct_answer", "").lower().strip()
                        acceptable = [v.lower().strip() for v in question.get("acceptable_variations", [])]
                        user_answer_lower = str(user_answer).lower().strip()

                        is_correct = (
                            user_answer_lower == correct_answer or
                            user_answer_lower in acceptable or
                            correct_answer in user_answer_lower
                        )

                    if is_correct:
                        correct_count += 1

                # Display score
                score_percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Score", f"{correct_count}/{total_questions}")
                with col2:
                    st.metric("Percentage", f"{score_percentage:.1f}%")
                with col3:
                    if score_percentage >= 80:
                        st.metric("Grade", "🌟 Excellent!")
                    elif score_percentage >= 60:
                        st.metric("Grade", "👍 Good")
                    else:
                        st.metric("Grade", "📚 Keep studying")

                st.markdown("---")

                # Display detailed results
                for idx, question in enumerate(questions):
                    user_answer_data = st.session_state.quiz_answers.get(idx, {})
                    user_answer = user_answer_data.get("answer", "")

                    q_text = question.get("question")
                    explanation = question.get("explanation", "")

                    # Determine if correct
                    if question["type"] == "multiple_choice":
                        correct_answer = question.get("correct")
                        is_correct = user_answer == correct_answer
                        options = question.get("options", {})
                    else:  # short_answer
                        correct_answer = question.get("correct_answer", "")
                        acceptable = [v.lower().strip() for v in question.get("acceptable_variations", [])]
                        user_answer_lower = str(user_answer).lower().strip()
                        correct_lower = correct_answer.lower().strip()

                        is_correct = (
                            user_answer_lower == correct_lower or
                            user_answer_lower in acceptable or
                            correct_lower in user_answer_lower
                        )

                    # Display result
                    if is_correct:
                        st.success(f"✅ Question {idx + 1}: Correct!")
                    else:
                        st.error(f"❌ Question {idx + 1}: Incorrect")

                    st.markdown(f"**{q_text}**")

                    if question["type"] == "multiple_choice":
                        st.markdown(f"**Your answer:** {user_answer}: {options.get(user_answer, 'Not answered')}")
                        if not is_correct:
                            st.markdown(f"**Correct answer:** {correct_answer}: {options.get(correct_answer)}")
                    else:
                        st.markdown(f"**Your answer:** {user_answer}")
                        if not is_correct:
                            st.markdown(f"**Expected answer:** {correct_answer}")

                    st.info(f"💡 **Explanation:** {explanation}")
                    st.markdown("---")

                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📝 Retake Quiz", type="primary"):
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_submitted = False
                        st.rerun()

                with col2:
                    if st.button("🎯 New Quiz"):
                        st.session_state.quiz_data = None
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_submitted = False
                        st.rerun()

    # Tips
    with st.expander("💡 Quiz Tips", expanded=False):
        st.markdown("""
        ### Question Types
        - **Multiple Choice**: Select from 4 options (A, B, C, D)
        - **Short Answer**: Type your answer in your own words

        ### Difficulty Levels
        - **Easy**: Basic recall of facts directly from the text
        - **Medium**: Understanding and application of concepts
        - **Hard**: Analysis, synthesis, and deep understanding

        ### Tips for Success
        - Read each question carefully
        - For short answers, be concise but complete
        - Review explanations after submitting to learn from mistakes
        - Try different difficulty levels to challenge yourself
        - Use "Single Document" mode to focus on specific topics
        - Use "All Documents" mode for comprehensive review

        ### Scoring
        - Multiple choice: Exact match required
        - Short answer: Flexible matching with acceptable variations
        - Review explanations to understand the correct answers
        """)

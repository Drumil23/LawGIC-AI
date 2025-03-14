# LawGIC - AI Legal Assistant

LawGIC-AI is an AI-powered legal assistant that provides answers based on the *Bharatiya Nyaya Sanhita (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS), and Bharatiya Sakshya Adhiniyam (BSA),  2023*. It allows users to ask legal questions and receive AI-driven responses, complete with references to the relevant sections of the law.

## Features

-   **AI-Powered Answers:** Get legal advice and information powered by the Gemini language model.
-   **Knowledge Base:** Trained on the *Bharatiya Nyaya Sanhita, (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS), and Bharatiya Sakshya Adhiniyam (BSA), 2023* to provide accurate and relevant answers.
-   **Custom Document Upload:** Upload your own legal proceedings in PDF format to expand the knowledge base.
-   **References:** Provides references to the specific sections of the law used to generate the answers.
-   **Interactive Chat Interface:** User-friendly chat interface for easy interaction with the legal assistant.

## Getting Started

### Prerequisites

-   Python 3.10+
-   pip
-   A Google Cloud project with the Gemini API enabled and an API key.
-   Qdrant vector database instance

### Installation

1.  Clone the repository:

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  Create a virtual environment:

    ```bash
    python -m venv chatbot-venv
    ```

3.  Activate the virtual environment:

    -   On Windows:

        ```bash
        .\chatbot-venv\Scripts\activate
        ```

    -   On macOS and Linux:

        ```bash
        source chatbot-venv/bin/activate
        ```

4.  Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

5.  Set up environment variables:

    Create a `.env` file in the root directory with the following variables:

    ```
    GOOGLE_API_KEY=<Your_Google_API_Key>
    QDRANT_COLLECTION=<Your_Qdrant_Collection_Name>
    QDRANT_URL=<Your_Qdrant_URL>
    QDRANT_API_KEY=<Your_Qdrant_API_Key>
    ```

    Replace the placeholder values with your actual API keys and database details.

### Usage

1.  Run the Streamlit application:

    ```bash
    streamlit run app.py
    ```

2.  Open the application in your browser at the address provided by Streamlit (usually `http://localhost:8501`).

3.  Start chatting with the legal assistant by typing your questions in the chat input.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues to suggest improvements or report bugs.

## Contact
For any inquiries, please contact drumil.kotecha@nmims.in




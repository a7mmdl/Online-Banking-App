# Integrated Online Banking System (Falcon-Finance-Bank)
## Ahmed Rafi - 2118961 - SEC 6201 - Undergraduate Project

## Overview 👨🏻‍💻
The online banking is a web-based application developed using Django, designed to meet various aspects of online banking. The application allows Online banking users to carry out banking tasks online without the need to visit a physical bank branch, all with an attractive and easy-to-use interface.

## Features ⚙️
- **Fund Transfer**: Transfer funds to your friends, relatives, etc., by just typing their account number and the amount.

- **Authentication/Registration**: Register yourself as a new banking customer online or login to the system to use all the unique features.

- **Withdraw/Deposit**: A unique feature added to withdraw or deposit cash right from the application, which later can be submitted or received from the branch but doing so adds or deducts the balance instantly.

- **Transaction History**: Keep track of all your transaction history, download as PDF, or just view our unique interactive and responsive line graph showing all the plus or minus in the account balance alongside with the date and time of the transaction.

- **Pay Bills**: View and pay all your bills (utility, electric, net, etc.) from our online banking platform, and the amount shall be deducted from your account balance.

## Built with 🛠️
- **Django**: A dynamic framework for crafting web applications used in the back-end development of this application.

- **HTML/CSS/JS**: Technologies used for the front-end development of this project (rendering Django-Templates).

- **FlowBite**: An Tailwind-css component library used to achieve polish results on front-end of this application giving user attractive and easy to use interface.

- **Stripe**: A famous world-wide used payment gateway allowing for secure and efficient transactions used in this application to provide users will features such as loan-repayment, card-issuance fees, Pay insurance fees, etc.

- **Tailwind CSS**: A utility-first CSS framework that streamlines web development by providing a vast array of pre-built classes for rapid styling, Helping us to reach the modern look for our app.

- **Streamlit**: The go-to platform for effortless creation of interactive data applications, enabling developers to transform data into engaging visualizations with just a few lines of code. Hosted our AI-Chatbot to assist banking-users

- **SQLite**: A lightweight yet powerful database engine seamlessly integrated into the Django framework, used to store our users-data such as transactions, account-balance securely and safely.

- **Google SMTP Server**: A reliable and secure email delivery service provided by Google, used to send user email during forget-password facility.


## Installation ⬇️
To set up and run the Falcon Finance Online Banking System on Local-Host, follow these steps:

1. Download the folder "TESTBANK" into your local machine.

2. Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

3. Apply database migrations:
    ```bash
    python manage.py migrate
    ```

4. Create a superuser account to access the admin panel:
    ```bash
    python manage.py createsuperuser
    ```

5. Install tailwind to build CSS (new terminal):
   
    5.1 Just run the following command:
        ```bash
        npm install
        ```

    5.2 Build the CSS using tailwindcss and continue looking for changes:
        ```bash
        npm run dev
        ```

6. Start the development server to run the website on localhost:
    ```bash
    python manage.py runserver
    ```

7. Access the Online Bank web-application using your web browser at http://localhost:8000. ✅

## Guidelines On Usage: 📖
### Admin Panel
- Access the admin panel at http://localhost:8000/admin using the superuser credentials created earlier. Here, you can manage users, their transactions, send notifications, view user inquiries, and many more.

## UI 👁️
### Home Page (dark)
[![HomePage.png](https://i.postimg.cc/W1Wmzszw/HomePage.png)](https://postimg.cc/21WLXR41)

### Home Page (light)
[![Home-Page-Light.png](https://i.postimg.cc/qv5yc0nB/Home-Page-Light.png)](https://postimg.cc/5X8X1hnD)

### AboutUs Page
[![AboutUs.png](https://i.postimg.cc/W1wWnd8m/AboutUs.png)](https://postimg.cc/rDzNyFvz)

### Login Page
[![Login-Page.png](https://i.postimg.cc/Njs7Qp8T/Login-Page.png)](https://postimg.cc/fJP0K7rT)

### Register Page
[![SignUp.png](https://i.postimg.cc/4yGHBxBt/SignUp.png)](https://postimg.cc/zbdff8mX)

### Online Banking Dashboard
[![Dash-Board.png](https://i.postimg.cc/bw4JmvvJ/Dash-Board.png)](https://postimg.cc/JscMnMZV)

### Fund Transfer Page 
[![Fund-Transfer.png](https://i.postimg.cc/fTcnGT5y/Fund-Transfer.png)](https://postimg.cc/svgNSzkC)

### Pay Bill Page 
[![PayBill.png](https://i.postimg.cc/mrq5c0VK/PayBill.png)](https://postimg.cc/d72BpNb9)

### ContactUs Page
[![Contact-Us.png](https://i.postimg.cc/Dy2Bzvn8/Contact-Us.png)](https://postimg.cc/yWbFQzJH)

## Contributing ✨
Contributions to this project are welcome! If you find a bug or have an enhancement in mind, please open an issue or create a pull request, or contact me on WhatsApp +971556683794.

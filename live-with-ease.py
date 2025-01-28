import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

url = "https://www.theblueground.com/furnished-apartments-toronto-canada?checkIn=2025-02-01&checkOut=2026-01-31"

def get_apartments(url, budget):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    apt_list = soup.find_all('a', class_="property")
    filtered_apts = []

    for apt in apt_list:
        url = apt.get('href')
        url = "https://www.theblueground.com/" + url
        price = apt.find('span', class_="price__amount").text.strip()
        building = apt.find('span', class_="property__name").text.strip()
        area = apt.find('span', class_="property__address").text.strip()
        price = float(price.replace(",", ""))
        if price < budget:
            filtered_apts.append({"url": url, "area": area, "building": building, "price": price})

    print(filtered_apts)
    return filtered_apts


def email_user(listings, user_email, user_password):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    subject = "Filtered Apartment Listings"
    body = "Here are the apartment listings within your budget:\n\n"

    for listing in listings:
        body += f"Building: {listing['building']}\n"
        body += f"Area: {listing['area']}\n"
        body += f"Price: ${listing['price']}\n"
        body += f"Link: {listing['url']}\n\n"

    msg = MIMEMultipart()
    msg['From'] = user_email
    msg['To'] = user_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(user_email, user_password)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {user_email} successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

budget = int(input("Enter your budget (in CAD): "))
filtered_apts = get_apartments(url, budget)
if filtered_apts:
    user_email = input("Enter your email: ") 
    user_password = input("Enter your APP password: ")

    email_user(filtered_apts, user_email, user_password)
else:
    print("No listings found within the specified budget.")
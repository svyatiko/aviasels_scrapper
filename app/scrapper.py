import json
from page_loader import PageLoader
from time import sleep
from bs4 import BeautifulSoup
import datetime
from retry import retry

COUNTRIES = ["poland", "latvia", "thailand", "lithuania", "norway", "spain"]
RU_MONTH_VALUES = {
    "янв": "01",
    "фев": "02",
    "мар": "03",
    "апр": "04",
    "мая": "05",
    "июн": "06",
    "июл": "07",
    "авг": "08",
    "сен": "09",
    "окт": "10",
    "ноя": "11",
    "дек": "12",
}
# https://www.aviasales.by/search/MSQ{date}WAW1?utm_adgroup_id=127673552544&utm_campaign=by_minsk_desktop_search_brand_new_users&utm_campaign_id=12740185866&utm_content_id=570631537394&utm_medium=cpc&utm_source=ga&utm_term=aviasales&utm_term_id=kwd-42393665022&request_source=search_form&expected_price_value=1750&expected_price_currency=byn&expected_price_source=calendar&payment_method=all

def get_url(country, date):
    URLS = {
        "poland": f"https://www.aviasales.by/search/MSQ{date}WAW1?utm_adgroup_id=127673552544&utm_campaign=by_minsk_desktop_search_brand_new_users&utm_campaign_id=12740185866&utm_content_id=570631537394&utm_medium=cpc&utm_source=ga&utm_term=aviasales&utm_term_id=kwd-42393665022&request_source=search_form&expected_price_value=4705&expected_price_currency=byn&expected_price_source=calendar&payment_method=all",
        "latvia": f"https://www.aviasales.by/search/MSQ{date}RIX1?utm_adgroup_id=127673552544&utm_campaign=by_minsk_desktop_search_brand_new_users&utm_campaign_id=12740185866&utm_content_id=570631537394&utm_medium=cpc&utm_source=ga&utm_term=aviasales&utm_term_id=kwd-42393665022&request_source=search_form&expected_price_value=1429&expected_price_currency=byn&expected_price_source=calendar&payment_method=all",
        "thailand": f"https://www.aviasales.by/search/MSQ{date}BKK1?utm_adgroup_id=127673552544&utm_campaign=by_minsk_desktop_search_brand_new_users&utm_campaign_id=12740185866&utm_content_id=570631537394&utm_medium=cpc&utm_source=ga&utm_term=aviasales&utm_term_id=kwd-42393665022&request_source=search_form&expected_price_value=2820&expected_price_currency=byn&expected_price_source=calendar&payment_method=all",
        "lithuania": f"https://www.aviasales.by/search/MSQ{date}VNO1?utm_adgroup_id=127673552544&utm_campaign=by_minsk_desktop_search_brand_new_users&utm_campaign_id=12740185866&utm_content_id=570631537394&utm_medium=cpc&utm_source=ga&utm_term=aviasales&utm_term_id=kwd-42393665022&request_source=search_form&expected_price_value=1624&expected_price_currency=byn&expected_price_source=calendar&payment_method=all",
        "norway": f"https://www.aviasales.by/search/MSQ{date}OSL1?utm_adgroup_id=127673552544&utm_campaign=by_minsk_desktop_search_brand_new_users&utm_campaign_id=12740185866&utm_content_id=570631537394&utm_medium=cpc&utm_source=ga&utm_term=aviasales&utm_term_id=kwd-42393665022&request_source=search_form&expected_price_currency=byn&expected_price_source=calendar&payment_method=all",
        "spain": f"https://www.aviasales.by/search/MSQ{date}MAD1?utm_adgroup_id=127673552544&utm_campaign=by_minsk_desktop_search_brand_new_users&utm_campaign_id=12740185866&utm_content_id=570631537394&utm_medium=cpc&utm_source=ga&utm_term=aviasales&utm_term_id=kwd-42393665022&request_source=search_form&expected_price_currency=byn&expected_price_source=calendar&payment_method=all",
    }

    return URLS[country]


def ticket_exist(soup):
    error_msg = soup.find("div", class_="error-informer__container")
    content = error_msg.contents[0]
    return content


def get_departure_date(day_delta):
    today = datetime.datetime.now()
    date_change = datetime.timedelta(days=day_delta)
    departure_date = today + date_change

    month = str(departure_date.month)
    day = str(departure_date.day)
    date = f'{day if len(day)==2 else "0"+day}{month if len(month)==2 else "0"+month}'
    return date


def not_simple_tickets_exist(soup):
    not_simple_tickets = []
    try:
        for i in range(2):
            content = (
                soup[i]
                .find(
                    "span",
                    class_="body-3-semi_03dd9f9 mobile-body-3-semi_03dd9f9 single-line_03dd9f9 text_34b0c12",
                )
                .contents
            )
            not_simple_tickets.append(content[0])
    except:
        pass
    return not_simple_tickets



@retry(exceptions=Exception,delay=5)
def scrap_one_day(day, country, loader):
    date = get_departure_date(day)
    url = get_url(country, date)
    page = loader.load_page(url)

    soup = BeautifulSoup(page, "html.parser")
    date = date[:2] + "." + date[2:]
    # ticket check
    try:
        ticket_exist(soup)
        return [{"error": "Билетов нет"}], date
    except:
        all_tickets = soup.find_all(
            "div", class_="product-list__item fade-appear-done fade-enter-done"
        )

        not_simple_tickets = not_simple_tickets_exist(all_tickets)

        tickets = (
            [all_tickets[0], all_tickets[1]]
            if len(all_tickets) >= 2
            else [all_tickets[0]]
        )
        data = unity_tickets_data(tickets, not_simple_tickets, url)
        print(f'Country: "{country}" for date: "{date}": SCRAPPED DONE ✓✓✓')
        return data, date

# @retry(exceptions=Exception,delay=5)
def scrap_country_tickets(country, loader):
    weekly_data = {}
    print("------------------------------------")

    # get ticketes on range = week
    for day in range(8):
        data, date= scrap_one_day(day, country, loader)
        weekly_data[date] = data

    return weekly_data


def get_departure_and_arrival_info(ticket):
    departure_info = []
    arrival_info = []
    data = {}

    departure_class_content = ticket.find(
        "div", class_="segment-route__endpoint origin"
    ).contents
    for i in departure_class_content:
        departure_info.append(i.contents[0])

    arrival_class_content = ticket.find(
        "div", class_="segment-route__endpoint destination"
    ).contents
    for i in arrival_class_content:
        arrival_info.append(i.contents[0])

    departure_date, departure_day = date_conversion(departure_info[2])
    data["departure_info"] = {
        "departure_time": departure_info[0],
        "departure_city": departure_info[1],
        "departure_date": departure_date,
        "departure_day": departure_day,
    }
    arrival_date, arrival_day = date_conversion(arrival_info[2])
    data["arrival_info"] = {
        "arrival_time": arrival_info[0],
        "arrival_city": arrival_info[1],
        "arrival_date": arrival_date,
        "arrival_day": arrival_day,
    }

    return data


def date_conversion(date):
    date_str, day = date.split(",")
    for k, v in RU_MONTH_VALUES.items():
        date_str = date_str.replace(k, str(v))
    year = str(datetime.datetime.now().year)[-2:]

    updated_date = date_str[:2] + "." + date_str[2:] + "." + year

    updated_date = updated_date.replace(" ", "")
    day = day.replace(" ", "")
    return updated_date, day


def create_union_ticket_data(ticket, index, not_simple_tickets, url):
    departure_and_arrival_info = get_departure_and_arrival_info(ticket)
    try:
        ticket_type = not_simple_tickets[index]
    except:
        ticket_type = "Обычный билет"

    data = {
        "cost": get_ticket_cost(ticket) + "Br",
        "travel_time": get_travel_time(ticket),
        "ticket_type": ticket_type,
        **departure_and_arrival_info,
        "url": url,
    }

    return data


def get_ticket_cost(ticket):
    class_content = ticket.find("span", class_="price_85d2b9c").contents
    price = class_content[0]
    return price


def get_travel_time(ticket):
    class_content = ticket.find("div", class_="segment-route__duration").contents
    travel_time = class_content[0]
    travel_time = travel_time[9:]
    return travel_time


def unity_tickets_data(tickets, not_simple_tickets, url):
    data = []
    for index, ticket in enumerate(tickets):
        ticket_data = create_union_ticket_data(ticket, index, not_simple_tickets, url)
        data.append(ticket_data)

    return data


def main():
    sleep(10)
    data = {}
    loader = PageLoader()
    for country in COUNTRIES:
        country_tickets = scrap_country_tickets(country, loader)
        data[country] = country_tickets

    with open("data_tickets.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("DONE!!!!!!!!!!!!!!!!!!")


if __name__ == "__main__":
    main()

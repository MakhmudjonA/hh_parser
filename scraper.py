import re
import time
import urllib.parse
from typing import Dict, List, Optional, Any, Callable
import requests
from bs4 import BeautifulSoup
import pandas as pd

class HHScraper:
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        })
        self.is_authenticated = False
        self.auth_user = None
        self.last_captcha_url = None
        self.last_captcha_bytes = None

    def parse_salary(self, text: str) -> Dict[str, Any]:
        """Parse salary text into min, max, currency, and display text."""
        clean = text.replace('\xa0', ' ').replace('\u202f', ' ').strip()
        if not clean or clean.lower() in ["not specified", "до вычета налогов", "на руки", "ko'rsatilmagan"]:
            return {"raw": "Not specified", "min": None, "max": None, "currency": None}

        currency = "UZS"
        if "$" in clean or "USD" in clean:
            currency = "USD"
        elif "€" in clean or "EUR" in clean:
            currency = "EUR"
        elif "₽" in clean or "руб" in clean:
            currency = "RUB"
        elif "сум" in clean:
            currency = "UZS"

        # Extract all numbers
        # E.g. "1 000 – 2 000 $" or "from 15 000 000"
        numbers = re.findall(r'(\d[\d\s]*\d|\d+)', clean)
        cleaned_numbers = []
        for n in numbers:
            num_str = n.replace(' ', '')
            if num_str.isdigit():
                cleaned_numbers.append(int(num_str))

        sal_min = None
        sal_max = None
        if len(cleaned_numbers) == 1:
            if any(w in clean.lower() for w in ["от", "from"]):
                sal_min = cleaned_numbers[0]
            elif any(w in clean.lower() for w in ["до", "up to", "to"]):
                sal_max = cleaned_numbers[0]
            else:
                sal_min = cleaned_numbers[0]
        elif len(cleaned_numbers) >= 2:
            sal_min = cleaned_numbers[0]
            sal_max = cleaned_numbers[1]

        return {
            "raw": clean,
            "min": sal_min,
            "max": sal_max,
            "currency": currency
        }

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch URL with session and return BeautifulSoup parsed HTML."""
        try:
            resp = self.session.get(url, timeout=12)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, "html.parser")
            elif resp.status_code in (403, 429):
                print(f"Warning: HH rate limit or captcha challenge (HTTP {resp.status_code})")
                return None
            else:
                print(f"Error fetching {url}: status {resp.status_code}")
                return None
        except Exception as e:
            print(f"Request exception for {url}: {e}")
            return None

    def search_vacancies(
        self,
        query: str,
        area: str = "2759", # Default: Tashkent
        salary_from: Optional[int] = None,
        experience: Optional[str] = None,
        employment: Optional[str] = None,
        schedule: Optional[str] = None,
        pages: int = 1,
        fetch_details: bool = False,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape vacancies from hh.uz based on query and filters.
        """
        results = []
        base_url = "https://hh.uz/search/vacancy"

        for page in range(pages):
            params = {
                "text": query.strip(),
                "area": str(area) if area else "2759",
                "page": str(page),
                "hhtmFrom": "vacancy_search_list"
            }
            if salary_from:
                params["salary"] = str(salary_from)
            if experience:
                params["experience"] = experience
            if employment:
                params["employment"] = employment
            if schedule:
                params["schedule"] = schedule

            page_url = f"{base_url}?{urllib.parse.urlencode(params)}"
            if progress_callback:
                progress_callback({
                    "status": "fetching_page",
                    "current_page": page + 1,
                    "total_pages": pages,
                    "message": f"Requesting page {page + 1} of {pages}...",
                    "count": len(results)
                })

            soup = self.fetch_page(page_url)
            if not soup:
                break

            # Find all vacancy cards (semantic article or data-qa='vacancy-serp__vacancy')
            cards = soup.find_all(attrs={"data-qa": "vacancy-serp__vacancy"})
            if not cards:
                # Fallback to serp-item
                cards = soup.find_all("article", class_=lambda x: x and "magritte-card" in x)

            if not cards:
                if progress_callback:
                    progress_callback({
                        "status": "no_more_results",
                        "current_page": page + 1,
                        "total_pages": pages,
                        "message": f"No more vacancies found on page {page + 1}.",
                        "count": len(results)
                    })
                break

            for card in cards:
                try:
                    # Title & Link
                    title_el = card.find(attrs={"data-qa": "serp-item__title"})
                    if not title_el:
                        continue
                    
                    title = title_el.text.strip()
                    link = title_el.get("href", "")
                    if link.startswith("/"):
                        link = "https://hh.uz" + link
                    
                    # Extract vacancy ID
                    vac_id_match = re.search(r'/vacancy/(\d+)', link)
                    vac_id = vac_id_match.group(1) if vac_id_match else str(len(results) + 1)

                    # Employer / Company
                    comp_el = (
                        card.find(attrs={"data-qa": "vacancy-serp__vacancy-employer-text"}) or 
                        card.find(attrs={"data-qa": "vacancy-serp__vacancy-employer"})
                    )
                    company = comp_el.text.strip() if comp_el else "Unknown Company"
                    company_url = comp_el.get("href", "") if comp_el and comp_el.name == "a" else ""
                    if company_url and company_url.startswith("/"):
                        company_url = "https://hh.uz" + company_url

                    # Employer Logo
                    logo_img = card.find("img", attrs={"data-qa": lambda x: x and "logo" in str(x)})
                    logo_url = logo_img.get("src", "") if logo_img else ""

                    # Salary
                    salary_str = "Not specified"
                    for el in card.find_all(["span", "div"]):
                        t = el.text.strip()
                        if any(c in t for c in ["сум", "$", "USD", "руб", "EUR", "₽"]) and len(t) < 60:
                            salary_str = t
                            break
                    salary_info = self.parse_salary(salary_str)

                    # Experience
                    exp_el = card.find(attrs={"data-qa": lambda x: x and "experience" in str(x)})
                    experience_str = exp_el.text.strip() if exp_el else "Not specified"

                    # Address / Metro / District
                    addr_el = card.find(attrs={"data-qa": "vacancy-serp__vacancy-address"})
                    address = addr_el.text.strip() if addr_el else "Tashkent"

                    # Tags / Badges (Remote, Urgent, etc.)
                    tags = []
                    badge_els = card.find_all(attrs={"data-qa": lambda x: x and ("label" in str(x) or "badge" in str(x))})
                    for b in badge_els:
                        bt = b.text.strip()
                        if bt and len(bt) < 30 and bt not in tags:
                            tags.append(bt)

                    item = {
                        "id": vac_id,
                        "title": title,
                        "company": company,
                        "company_url": company_url,
                        "company_logo": logo_url,
                        "salary": salary_info["raw"],
                        "salary_min": salary_info["min"],
                        "salary_max": salary_info["max"],
                        "currency": salary_info["currency"],
                        "experience": experience_str,
                        "address": address,
                        "tags": tags,
                        "link": link,
                        "skills": [],
                        "description": "",
                        "email": "N/A",
                        "phone": "N/A"
                    }

                    results.append(item)
                except Exception as ex:
                    print(f"Error parsing vacancy card: {ex}")
                    continue

            # Sleep between pages to avoid throttling
            time.sleep(0.5)

        # Optionally fetch details for each vacancy (skills, description, contacts)
        if fetch_details and results:
            total_items = len(results)
            for idx, item in enumerate(results):
                if progress_callback:
                    progress_callback({
                        "status": "fetching_details",
                        "current_item": idx + 1,
                        "total_items": total_items,
                        "message": f"Fetching details ({idx + 1}/{total_items}): {item['title'][:30]}...",
                        "count": len(results)
                    })
                
                detail_soup = self.fetch_page(item["link"])
                if detail_soup:
                    desc_el = detail_soup.find(attrs={"data-qa": "vacancy-description"})
                    if desc_el:
                        full_desc = desc_el.text.strip()
                        item["description"] = full_desc[:500] + ("..." if len(full_desc) > 500 else "")
                        
                        # Find emails and phones in description
                        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', full_desc)
                        phones = re.findall(r'(\+?998[\s-]?\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2})', full_desc)
                        if emails:
                            item["email"] = emails[0]
                        if phones:
                            item["phone"] = phones[0]

                    # Skills
                    skill_badges = detail_soup.find_all(attrs={"data-qa": lambda x: x and "skills" in str(x)})
                    item["skills"] = [s.text.strip() for s in skill_badges if s.text.strip()]

                time.sleep(0.3)

        if progress_callback:
            progress_callback({
                "status": "completed",
                "total_pages": pages,
                "message": f"Successfully completed! Found {len(results)} vacancies.",
                "count": len(results)
            })

        return results

    def to_dataframe(self, vacancies: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert list of vacancy dicts to Pandas DataFrame with English headers."""
        rows = []
        for v in vacancies:
            rows.append({
                "ID": v.get("id"),
                "Job Title": v.get("title"),
                "Company": v.get("company"),
                "Salary": v.get("salary"),
                "Experience": v.get("experience"),
                "Location": v.get("address"),
                "Key Skills": ", ".join(v.get("skills", [])),
                "Email": v.get("email"),
                "Phone": v.get("phone"),
                "Tags": ", ".join(v.get("tags", [])),
                "Link": v.get("link")
            })
        return pd.DataFrame(rows)

    def export_csv(self, vacancies: List[Dict[str, Any]], filepath: str) -> str:
        """Export to CSV with UTF-8 BOM so Excel opens English/Cyrillic properly."""
        df = self.to_dataframe(vacancies)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        return filepath

    def export_excel(self, vacancies: List[Dict[str, Any]], filepath: str) -> str:
        """Export to Excel .xlsx format."""
        df = self.to_dataframe(vacancies)
        df.to_excel(filepath, index=False, engine='openpyxl')
        return filepath

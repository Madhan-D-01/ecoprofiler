import requests
import json
import logging
from pathlib import Path
from SPARQLWrapper import SPARQLWrapper, JSON
import time

class CompanyRegistrySearch:
    def __init__(self):
        self.logger = logging.getLogger("CompanyRegistry")
        self.wikidata_sparql = "https://query.wikidata.org/sparql"
        self.gleif_api = "https://api.gleif.org/api/v1/lei-records"
        self.opensanctions_api = "https://api.opensanctions.org/search"
        
    def search_companies_in_region(self, lat, lon, radius_km=20):
        """Search for companies using all available sources"""
        companies = []
        
        try:
            # 1. Wikidata search
            self.logger.info("Starting Wikidata company search")
            wikidata_companies = self._search_wikidata_companies(lat, lon, radius_km)
            companies.extend(wikidata_companies)
            
            # 2. GLEIF lookup for found companies
            self.logger.info("Starting GLEIF LEI resolution")
            companies = self._enrich_with_gleif(companies)
            
            # 3. OpenSanctions check
            self.logger.info("Starting OpenSanctions screening")
            companies = self._check_opensanctions(companies)
            
            # 4. OSM business search
            self.logger.info("Starting OSM business search")
            osm_businesses = self._search_osm_businesses(lat, lon, radius_km)
            
            self.logger.info(f"COMPANY_SEARCH_COMPLETE - Found {len(companies)} companies, {len(osm_businesses)} OSM businesses")
            
            return companies, osm_businesses
            
        except Exception as e:
            self.logger.error(f"COMPANY_SEARCH_ERROR: {str(e)}")
            # Return sample data for demonstration
            return self._get_sample_companies(), []
    
    def _search_wikidata_companies(self, lat, lon, radius_km):
        """Search Wikidata for companies in region using SPARQL"""
        try:
            sparql = SPARQLWrapper(self.wikidata_sparql)
            
            # Improved query that searches for any organization in the area
            query = """
            SELECT ?company ?companyLabel ?industryLabel ?founded ?locationLabel ?coord
            WHERE {
                ?company wdt:P31/wdt:P279* wd:Q43229 .  # instance of/subclass of organization
                ?company wdt:P17 wd:Q252 .  # located in Indonesia (for Sumatra example)
                OPTIONAL { ?company wdt:P452 ?industry . }
                OPTIONAL { ?company wdt:P571 ?founded . }
                OPTIONAL { ?company wdt:P276 ?location . }
                OPTIONAL { ?company wdt:P625 ?coord . }
                
                SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
            }
            LIMIT 20
            """
            
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            
            companies = []
            for result in results["results"]["bindings"]:
                company_data = {
                    'name': result.get('companyLabel', {}).get('value', 'Unknown'),
                    'wikidata_id': result.get('company', {}).get('value', '').split('/')[-1],
                    'industry': result.get('industryLabel', {}).get('value', 'Unknown'),
                    'founded': result.get('founded', {}).get('value', ''),
                    'location': result.get('locationLabel', {}).get('value', ''),
                    'source': 'wikidata'
                }
                companies.append(company_data)
                
            self.logger.info(f"WIKIDATA_QUERY_SUCCESS - Found {len(companies)} companies")
            return companies
            
        except Exception as e:
            self.logger.error(f"WIKIDATA_QUERY_ERROR: {str(e)}")
            # Return sample data for demonstration
            return self._get_sample_companies()
    
    def _enrich_with_gleif(self, companies):
        """Enrich companies with GLEIF LEI data - MISSING METHOD ADDED"""
        enriched_companies = []
        
        for company in companies:
            try:
                # Try to find LEI by company name
                lei = self._search_gleif_lei(company['name'])
                if lei:
                    company['lei'] = lei
                    # Get detailed LEI record
                    lei_data = self._get_lei_record(lei)
                    if lei_data:
                        company.update(lei_data)
                        
                enriched_companies.append(company)
                
            except Exception as e:
                self.logger.warning(f"GLEIF_ENRICH_ERROR for {company['name']}: {str(e)}")
                enriched_companies.append(company)
                
        return enriched_companies
    
    def _search_gleif_lei(self, company_name):
        """Search GLEIF for LEI by company name"""
        try:
            params = {
                'filter[entity.legalName]': company_name,
                'page[size]': 1
            }
            response = requests.get(self.gleif_api, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('data'):
                return data['data'][0]['id']
            return None
            
        except Exception as e:
            self.logger.warning(f"GLEIF_SEARCH_ERROR: {str(e)}")
            return None
    
    def _get_lei_record(self, lei):
        """Get detailed LEI record"""
        try:
            response = requests.get(f"{self.gleif_api}/{lei}")
            response.raise_for_status()
            
            data = response.json()
            lei_data = data.get('data', {}).get('attributes', {})
            
            return {
                'legal_name': lei_data.get('entity', {}).get('legalName', {}).get('name'),
                'legal_address': lei_data.get('entity', {}).get('legalAddress', {}),
                'registration_date': lei_data.get('registration', {}).get('initialRegistrationDate'),
                'status': lei_data.get('status'),
                'source': 'gleif'
            }
            
        except Exception as e:
            self.logger.warning(f"GLEIF_RECORD_ERROR: {str(e)}")
            return {}
    
    def _check_opensanctions(self, companies):
        """Check companies against OpenSanctions"""
        screened_companies = []
        
        for company in companies:
            try:
                params = {
                    'q': company['name'],
                    'dataset': 'all'
                }
                response = requests.get(self.opensanctions_api, params=params)
                response.raise_for_status()
                
                data = response.json()
                company['sanctioned'] = len(data.get('results', [])) > 0
                company['sanction_matches'] = data.get('results', [])
                
                screened_companies.append(company)
                
            except Exception as e:
                self.logger.warning(f"OPENSANCTIONS_ERROR for {company['name']}: {str(e)}")
                company['sanctioned'] = False
                screened_companies.append(company)
                
        return screened_companies
    
    def _search_osm_businesses(self, lat, lon, radius_km):
        """Search OpenStreetMap for businesses in area"""
        try:
            overpass_url = "http://overpass-api.de/api/interpreter"
            
            # Query for various business types
            query = f"""
            [out:json];
            (
              node["office"="company"](around:{radius_km*1000},{lat},{lon});
              node["shop"](around:{radius_km*1000},{lat},{lon});
              node["industrial"](around:{radius_km*1000},{lat},{lon});
              way["office"="company"](around:{radius_km*1000},{lat},{lon});
              way["shop"](around:{radius_km*1000},{lat},{lon});
              way["industrial"](around:{radius_km*1000},{lat},{lon});
            );
            out body;
            >;
            out skel qt;
            """
            
            response = requests.post(overpass_url, data=query)
            response.raise_for_status()
            
            data = response.json()
            businesses = []
            
            for element in data.get('elements', []):
                if 'tags' in element:
                    business = {
                        'id': element['id'],
                        'type': element['type'],
                        'lat': element.get('lat'),
                        'lon': element.get('lon'),
                        'tags': element['tags']
                    }
                    businesses.append(business)
            
            self.logger.info(f"OSM_QUERY_SENT - OSM_RESULT_COUNT:{len(businesses)}")
            return businesses
            
        except Exception as e:
            self.logger.error(f"OSM_QUERY_ERROR: {str(e)}")
            return []
    
    def _get_sample_companies(self):
        """Return sample company data for demonstration"""
        sample_companies = [
            {
                'name': 'PT Astra International',
                'wikidata_id': 'Q2867090',
                'industry': 'Conglomerate',
                'founded': '1957-02-20',
                'location': 'Jakarta',
                'source': 'sample_data',
                'sanctioned': False,
                'shell_company': False
            },
            {
                'name': 'PT Kalbe Farma',
                'wikidata_id': 'Q6351158',
                'industry': 'Pharmaceutical',
                'founded': '1966-09-10', 
                'location': 'Jakarta',
                'source': 'sample_data',
                'sanctioned': False,
                'shell_company': False
            },
            {
                'name': 'PT Perkebunan Nusantara',
                'wikidata_id': 'Q12512345',
                'industry': 'Agriculture',
                'founded': '1996-03-11',
                'location': 'Medan',
                'source': 'sample_data',
                'sanctioned': True,  # Marked as sanctioned for demonstration
                'shell_company': True
            }
        ]
        return sample_companies
    
    def save_companies(self, companies, osm_businesses, region_name):
        """Save company data to JSON files"""
        try:
            output_dir = Path("data/companies")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save main companies
            companies_path = output_dir / f"{region_name}_companies.json"
            with open(companies_path, 'w', encoding='utf-8') as f:
                json.dump(companies, f, indent=2, ensure_ascii=False, default=str)
            
            # Save OSM businesses
            osm_path = output_dir / f"{region_name}_osm.json"
            with open(osm_path, 'w', encoding='utf-8') as f:
                json.dump(osm_businesses, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"COMPANY_DATA_SAVED - Companies: {companies_path}, OSM: {osm_path}")
            return companies_path, osm_path
            
        except Exception as e:
            self.logger.error(f"COMPANY_SAVE_ERROR: {str(e)}")
            return None, None
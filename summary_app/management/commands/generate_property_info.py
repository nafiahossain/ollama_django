from django.core.management.base import BaseCommand
from django.db import transaction
from config import Property, OLLAMA_API_URL
from summary_app.models import Summary
import requests
import json


class Command(BaseCommand):
    help = 'Rewrites property information using Ollama API'

    def handle(self, *args, **options):
        ollama_url = OLLAMA_API_URL

        properties = Property.objects.all()
        for property in properties:
            self.stdout.write(f"Processing property {property.property_id}")

            # Rewrite title and description
            prompt = f"""
            Please rewrite the following property title and description to make them more engaging, appealing, and descriptive. 
            Ensure that the title is concise yet catchy, and that the description highlights the key features in a clear and compelling manner. 
            Generate only one title and one description without adding any extra text, markdown formatting, or symbols. 
            Always format your response strictly as follows: Title: and Description:
            
            Original Title: {property.title}
            Original Description: {property.description}
            """

            response = self.generate_ollama(ollama_url, prompt)
            
            if not response:
                self.stdout.write(self.style.ERROR(f"Skipping property {property.property_id} due to API error"))
                continue

            new_content = ''.join([r.get('response', '') for r in response]).strip()

            # More robust parsing
            try:
                new_title, new_description = self.parse_content(new_content)
            except ValueError as e:
                self.stdout.write(self.style.ERROR(f"Error parsing content for property {property.property_id}: {str(e)}"))
                self.stdout.write(f"Received content: {new_content}")
                continue

            # Generate summary
            summary_prompt = f"Summarize the following property information:\nTitle: {new_title}\nDescription: {new_description}\nRating: {property.rating}\nLocation: {property.locations}\nAmenities: {', '.join(str(a) for a in property.amenities.all())}"
            summary_response = self.generate_ollama(ollama_url, summary_prompt)
            
            if not summary_response:
                self.stdout.write(self.style.ERROR(f"Skipping summary for property {property.property_id} due to API error"))
                continue

            summary_text = ' '.join([r.get('response', '').strip() for r in summary_response]).strip()


            # Update database
            try:
                with transaction.atomic():
                    property.title = new_title
                    property.description = new_description
                    property.save()

                    Summary.objects.update_or_create(
                        property=property,
                        defaults={'summary': summary_text}
                    )

                self.stdout.write(self.style.SUCCESS(f"Updated property {property.property_id}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error updating property {property.property_id}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS('All properties processed'))

    def generate_ollama(self, url, prompt):
        payload = {
            "model": "gemma2:2b",
            "prompt": prompt
        }
        try:
            response = requests.post(url, json=payload, stream=True)
            response.raise_for_status()
            # Log the raw response for debugging
            #self.stdout.write(f"Raw API response: {response.text}")
            # Parse multiple JSON objects
            json_objects = self.parse_json_stream(response.iter_lines())
            return json_objects
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Error communicating with Ollama API: {str(e)}"))
            return None

    def parse_json_stream(self, json_stream):
        decoder = json.JSONDecoder()
        objects = []
        buffer = ''
        for line in json_stream:
            buffer += line.decode('utf-8')
            while buffer:
                try:
                    result, index = decoder.raw_decode(buffer)
                    objects.append(result)
                    buffer = buffer[index:].strip()
                except json.JSONDecodeError:
                    break  # Stop if we can't parse any more valid JSON
        return objects

    def parse_content(self, content):
        # Split content into lines
        lines = content.strip().split('\n')
        
        new_title = ''
        new_description = ''
        
        for line in lines:
            if line.startswith('Title:'):
                new_title = line.replace('Title:', '').strip()
                # Remove unwanted characters like asterisks
                new_title = new_title.replace('*', '')
            elif line.startswith('Description:'):
                new_description = line.replace('Description:', '').strip()
        
        if not new_title or not new_description:
            raise ValueError("Could not parse title and description from content")
        
        return new_title, new_description

    
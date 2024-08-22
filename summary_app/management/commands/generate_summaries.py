
from django.core.management.base import BaseCommand
from property_app.models import Property
from summary_app.models import Summary


class Command(BaseCommand):
    help = 'Generate new title, description, and summary for properties using Ollama model'

    OLLAMA_URL = 'http://localhost:11434/api/generate'

    def handle(self, *args, **options):
        # Fetch all properties using Django ORM
        properties = Property.objects.all()

        for prop in properties:
            # Generate new title using Ollama
            new_title = self.generate_text(f"Rewrite the following property title: {prop.title}")

            # Generate new description using the original title
            new_description = self.generate_text(f"Rewrite the following property description based on title '{prop.title}': {prop.description}")

            # Update the property with new title and description
            prop.title = new_title
            prop.description = new_description
            prop.save()

            # Prepare property information for summary generation
            property_info = f"""
            Title: {new_title}
            Description: {new_description}
            Rating: {prop.rating}
            Location: {prop.locations.name}
            Amenities: {', '.join([a.name for a in prop.amenities.all()])}
            """

            # Generate summary using Ollama
            summary_text = self.generate_text(f"Generate a summary for the following property information: {property_info}")

            # Save the summary in the Summary table
            summary, created = Summary.objects.get_or_create(property=prop)
            summary.summary = summary_text
            summary.save()

        self.stdout.write(self.style.SUCCESS('Successfully generated new titles, descriptions, and summaries for properties.'))

    

    def generate_text(self, prompt):
        """Send the prompt to Ollama and return the generated text."""
        import requests
        import json
        try:
            # Send the POST request
            response = requests.post(self.OLLAMA_URL, json={"model": "gemma2:2b", "prompt": prompt}, stream=True)
            response.raise_for_status()  # Check if the request was successful
            
            # Log the raw response text
            print("Raw response text:", response.text)
            
            # Handle multiple JSON objects in the response
            combined_response = response.text.strip()
            
            # Combine JSON objects if they are in multiple lines
            responses = []
            for line in combined_response.splitlines():
                try:
                    # Attempt to parse each line as a JSON object
                    json_obj = json.loads(line)
                    responses.append(json_obj)
                except json.JSONDecodeError:
                    # If a line is not valid JSON, you can decide how to handle it
                    print(f"Skipping invalid JSON line: {line}")
            
            # Assuming the 'output' is in the last JSON object in the list
            if responses:
                last_response = responses[-1]
                return last_response.get('response', '').strip()
            
            return ""
        except requests.exceptions.RequestException as e:
            self.stderr.write(f"Failed to generate text: {str(e)}")
            return ""


'''
from django.core.management.base import BaseCommand
from property_app.models import Property
from summary_app.models import Summary
import requests
import json
from django.db import transaction

class Command(BaseCommand):
    help = 'Generate new title, description, and summary for properties using Ollama model'

    OLLAMA_URL = 'http://localhost:11434/api/generate'

    def handle(self, *args, **options):
        properties = Property.objects.all()

        for prop in properties:
            new_title = self.generate_text(f"Rewrite the following property title: {prop.title}")

            if not new_title:
                self.stdout.write(self.style.WARNING(f"No new title generated for property ID {prop.property_id}"))
                continue

            new_description = self.generate_text(f"Rewrite the following property description based on title '{prop.title}': {prop.description}")

            if not new_description:
                self.stdout.write(self.style.WARNING(f"No new description generated for property ID {prop.property_id}"))
                continue

            # Wrap in a transaction to ensure all operations are committed
            try:
                with transaction.atomic():
                    # Truncate text if necessary
                    new_title = truncate_text(new_title, 255)
                    new_description = truncate_text(new_description, 255)

                    # Update property
                    prop.title = new_title
                    prop.description = new_description
                    prop.save()
                    self.stdout.write(self.style.SUCCESS(f"Updated property ID {prop.property_id} with new title and description."))

                    # Prepare property information for summary generation
                    property_info = f"""
                    Title: {new_title}
                    Description: {new_description}
                    Rating: {prop.rating}
                    Location: {', '.join([loc.name for loc in prop.locations.all()]) if prop.locations.exists() else 'N/A'}
                    Amenities: {', '.join([a.name for a in prop.amenities.all()])}
                    """

                    summary_text = self.generate_text(f"Generate a summary for the following property information: {property_info}")

                    if not summary_text:
                        self.stdout.write(self.style.WARNING(f"No summary generated for property ID {prop.property_id}"))
                        continue

                    # Save summary
                    summary, created = Summary.objects.get_or_create(property=prop)
                    summary.summary = truncate_text(summary_text, 1000)  # Example length for summary
                    summary.save()
                    self.stdout.write(self.style.SUCCESS(f"Saved summary for property ID {prop.property_id}."))

            except Exception as e:
                self.stderr.write(f"Error processing property ID {prop.property_id}: {str(e)}")

        self.stdout.write(self.style.SUCCESS('Successfully generated new titles, descriptions, and summaries for properties.'))


    def generate_text(self, prompt):
        """Send the prompt to Ollama and return the generated text."""
        import requests
        import json

        try:
            response = requests.post(self.OLLAMA_URL, json={"model": "gemma2:2b", "prompt": prompt}, stream=True)
            response.raise_for_status()

            complete_response = ""
            for chunk in response.iter_lines():
                if chunk:
                    try:
                        # Decode chunk as JSON
                        json_obj = json.loads(chunk.decode('utf-8'))
                        if 'response' in json_obj:
                            complete_response += json_obj['response']
                    except json.JSONDecodeError:
                        self.stderr.write(f"Skipping invalid JSON chunk: {chunk.decode('utf-8')}")

            if complete_response:
                return complete_response.strip()

            self.stderr.write("No valid response found in the API response.")
            return ""
        except requests.exceptions.RequestException as e:
            self.stderr.write(f"Failed to generate text: {str(e)}")
            return ""


import os
import json
import requests
from django.core.management.base import BaseCommand
from property_app.models import Property

class Command(BaseCommand):
    help = 'Generate property titles using the Ollama gemma2 model'

    def handle(self, *args, **kwargs):
        # API endpoint and headers
        endpoint = "http://localhost:11434/generate"
        headers = {"Content-Type": "application/json"}

        # Fetch all properties without titles
        properties = Property.objects.filter(title__isnull=True)
        
        for property in properties:
            # Prepare the data to send to the API
            data = {
                "input": f"Generate a title for the property located at {property.address}. The property is described as: {property.description}",
                "model": "gemma2:2b"
            }
            
            response = requests.post(endpoint, headers=headers, json=data)
            result = response.json()
            
            if 'response' in result:
                property.title = result['response']
                property.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully updated title for property {property.id}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to generate title for property {property.id}'))

'''
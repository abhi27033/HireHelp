def extract_data_from_txt(file_path):
    """
    Extract specific fields from a given text file.
    :param file_path: Path to the text file.
    :return: A dictionary containing the extracted data.
    """
    extracted_data = {
        'firstname': None,
        'lastname': None,
        'mobile': None,
        'email': None,
        'experience_years': None,
    }

    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            
        for line in lines:
            line = line.strip()
            
            # Extract first name
            if line.startswith("First Name:"):
                extracted_data['firstname'] = line.split(":", 1)[1].strip()
            
            # Extract last name
            elif line.startswith("Last Name:"):
                extracted_data['lastname'] = line.split(":", 1)[1].strip()
            
            # Extract mobile
            elif line.startswith("Mobile:"):
                extracted_data['mobile'] = line.split(":", 1)[1].strip()
            
            # Extract email
            elif line.startswith("Email:"):
                extracted_data['email'] = line.split(":", 1)[1].strip()
            
            # Extract experience years
            elif line.startswith("Experience:"):
                experience = line.split(":", 1)[1].strip()
                if experience.isdigit():  # Ensure it's a valid number
                    extracted_data['experience_years'] = int(experience)
        
        return extracted_data

    except Exception as e:
        return {'error': str(e)}

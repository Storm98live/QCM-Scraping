import streamlit as st
from lxml import html
import pandas as pd
from io import BytesIO

# Function to extract data from HTML using XPath
def extract_data_from_html(raw_html, xpath_expressions):
    tree = html.fromstring(raw_html)
    data = {}
    for key, xpath_expression in xpath_expressions.items():        
        
        if key == 'correction':
            data[key] = [element.split('\'')[3].replace("-" , "") for element in tree.xpath(xpath_expression)]
        
        elif key == 'session':
            data[key] = [element.text_content().strip().split(' ')[1] for element in tree.xpath(xpath_expression)]

        elif key == 'année':
            data[key] = [element.text_content().strip().split(' ')[0].split("  ")[1] for element in tree.xpath(xpath_expression)]

        elif key in ['module', 'sub_module']:
            elements = tree.xpath(xpath_expression)
            if elements:
                module, sub_module = elements[0].text.strip().split("(")
                data['sub_module'] = [module] * len(elements)
                data['module'] = [sub_module[:-1]] * len(elements)
            else:
                data[key] = []

        else:
            elements = tree.xpath(xpath_expression)
            if elements and isinstance(elements[0], html.HtmlElement):
                data[key] = [element.text_content().strip() for element in elements]
            else:
                data[key] = [element.strip() for element in elements]

    return data

# Define your XPath expressions to extract desired data from HTML
xpath_expressions = {
    'question': "//tbody//tr/td/p/b",
    'a' : "//span[contains(@id, 'choixA')]",
    'b' : "//span[contains(@id, 'choixB')]",
    'c' : "//span[contains(@id, 'choixC')]",
    'd' : "//span[contains(@id, 'choixD')]",
    'e' : "//span[contains(@id, 'choixE')]",
    'session' : "//tbody//tr//td//div/span[@class='sess color-blue' and not(contains(@style, 'top'))]",
    'année' : "//tbody//tr//td//div/span[@class='sess color-blue' and not(contains(@style, 'top'))]",
    'correction': "//button[contains(@onclick, 'getCor')]/@onclick",
    'cours' : "//div[contains(@style, 'color: white;')]/text()[normalize-space()]",
    'module': "//div[@class='page-title-heading']/div/div",
    'sub_module': "//div[@class='page-title-heading']/div/div"
}

st.title("HTML Data Extractor")

# Initialize HTML content in session state
if 'html_content' not in st.session_state:
    st.session_state.html_content = ""

html_input = st.text_area("Paste HTML Code Here", value=st.session_state.html_content)

add_button = st.button("Add")
export_button = st.button("Export")

# Filename input field
excel_filename = st.text_input("Enter Excel Filename (without extension)", value="extracted_data")

if add_button:
    # Extract data using XPath
    extracted_data = extract_data_from_html(html_input, xpath_expressions)
    
    if 'cours' in extracted_data:
        # Get the maximum length among all arrays
        max_length = max(len(value) for value in extracted_data.values())
        
        # Fill in empty lists with empty strings to match the maximum length
        for key, value in extracted_data.items():
            if len(value) == 0:
                extracted_data[key] = [''] * max_length

            elif len(value) < max_length and len(value) > 0:
                extracted_data[key] = [value[0]] * max_length

        # Create a DataFrame from the extracted data
        df_new = pd.DataFrame(extracted_data)
        
        # Check if there is already a stored dataframe in session state
        if 'data' not in st.session_state:
            st.session_state.data = df_new
        else:
            # Concatenate the new dataframe with the existing one and store it in session state
            st.session_state.data = pd.concat([st.session_state.data, df_new], ignore_index=True)

    # Clear text area after processing
    st.session_state.html_content = ""


if export_button:
    if 'data' in st.session_state:
        # Display the final DataFrame
        st.write("Preview of Final DataFrame:")
        st.write(st.session_state.data)
        
        # Export DataFrame to Excel
        excel_filename_with_extension = excel_filename + ".xlsx"
        excel_data = BytesIO()
        st.session_state.data.to_excel(excel_data, index=False)
        excel_data.seek(0)
        st.write("Click below button to download the Excel file:")
        st.download_button(label="Download Excel", data=excel_data, file_name=excel_filename_with_extension, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("No data available to export. Please add data first.")

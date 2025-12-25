import base64
import json
import os
import traceback
from pprint import pprint

import magic

import requests

from .common_config import MIME_TYPE_MAP


def submit_b2p_post_document_ticket(api_url, api_username, api_password, requested_for, substitute, company_code, ssf_category, short_description, document_date, posting_date,
                                    document_header_text, period, currency, document_type, posting_data, request, translation_date, cost_center='', reversal_date='',
                                    reason_for_reversal='', calculate_tax='true', country='CN', target_folder_name='', attachment_file_path_list=None, verify_ssl=True):
    """ This function is used to prepare and upload the data for B2P Post Document Ticket via ESM API.

    Args:
        api_url(str): This is the API URL for the B2P Post Document. e.g. https://gbs.bosch.com/api/robgh/esm_finance_catalog_api
        api_username(str): This is the API username for the B2P Post Document
        api_password(str): This is the API password for the B2P Post Document
        requested_for(str): This is the requested for user for the B2P Post Document
        substitute(str): This is the substitute for the B2P Post Document
        company_code(str): This is the company code for the B2P Post Document
        ssf_category(str): This is the SSF category for the B2P Post Document
        short_description(str): This is the short description for the B2P Post Document
        document_date(str): This is the document date for the B2P Post Document
        posting_date(str): This is the posting date for the B2P Post Document
        document_header_text(str): This is the document header text for the B2P Post Document
        period(str): This is the period for the B2P Post Document
        currency(str): This is the currency for the B2P Post Document
        document_type(str): This is the document type for the B2P Post Document
        posting_data(list[dict]): This is the list of posting data for the B2P Post Document.
        request(str): This is the request for the B2P Post Document
        translation_date(str): This is the translation date for the B2P Post Document
        cost_center(str): This is the cost center for the B2P Post Document
        reversal_date(str): This is the reversal date for the B2P Post Document
        reason_for_reversal(str): This is the reason for reversal for the B2P Post Document
        calculate_tax(str): This is the flag to calculate tax for the B2P Post Document
        country(str): This is the country for the B2P Post Document, default is 'CN'
        target_folder_name(str): This is the folder name that stores ssf attachments
        attachment_file_path_list(list): This is the list of attachment file paths for the B2P Post Document
        verify_ssl(bool|str): This is the flag to verify SSL for the B2P Post Document API request
    """
    try:
        response_dict = {}
        is_submit, ssf_number = True, ''
        attachment_file_path_list = attachment_file_path_list if attachment_file_path_list is not None else []
        attachment_file_list = []

        magic_tool = magic.Magic(mime=True)

        for attachment_file_path in attachment_file_path_list:
            ext = os.path.splitext(attachment_file_path)[1].upper()  # 提取文件扩展名并大写
            if ext in MIME_TYPE_MAP:
                content_type = MIME_TYPE_MAP[ext]
            else:
                # fallback 用 magic 自动识别
                content_type = magic_tool.from_file(attachment_file_path)
            file_name = os.path.basename(attachment_file_path)

            with open(attachment_file_path, "rb") as f:
                file_base64 = base64.b64encode(f.read()).decode("utf-8")
                print(len(file_base64) / 1024, "KB")

            attachment_file_list.append({
                'fileName': file_name,
                'contentType': content_type,
                'content': file_base64
            })

        api_data = {
            'variables': {
                "u_requested_for": requested_for,
                'u_multiple_substitutes': substitute,
                "u_ssf_company_code": company_code,
                "u_ssf_category": ssf_category,
                "u_specific_category": ssf_category,
                "u_cost_centers": cost_center,
                "short_description": short_description,
                "u_document_date": document_date,
                "u_period": period,
                "u_posting_date": posting_date,
                "u_document_header_text": document_header_text,
                "u_translation_date": translation_date,
                "u_currency": currency,
                "u_document_type": document_type,
                "u_reversal_date": reversal_date,
                "u_reason_for_reversal": reason_for_reversal,
                "u_calculate_tax": calculate_tax,
                "request": request,
                "u_country": country,
                "posting": posting_data,
                'attachments': []
            }
        }
        print('------------------------- api_data -------------------------')
        pprint(api_data)
        url = f'{api_url}/gle'

        # Eg. User name="admin", Password="admin" for this code sample.
        user = api_username
        pwd = api_password

        # Set proper headers
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        # Do the HTTP request
        response = requests.post(url, auth=(user, pwd), headers=headers, data=json.dumps(api_data), verify=verify_ssl)
        # Check for HTTP codes other than 200
        response_json = response.json()
        response_dict['ticket_response'] = [response_json]
        print(response.status_code)

        if response.status_code not in [200, 201]:
            pprint(response_json)
            is_submit = False
            error_list = response_json['result']['errorList']
            collected_error_list = [error_dict['message'] for error_dict in error_list]
            error_message = '\n'.join(collected_error_list)
            print(f'Errors occurs - {company_code} {cost_center} {target_folder_name}\n'
                  f'Please check your ESM posting data according to following error information:\n'
                  f'{error_message}')
        else:
            print(f'Ticket created for {company_code} {cost_center} {target_folder_name}')
            pprint(response_json)
            record = response_json['result']['record']
            if type(record) is dict:
                ssf_number = record['result']['number']
                table = record['result']['table']
                sys_id = record['result']['sys_id']
            else:
                record = json.loads(record)
                ssf_number = record['result']['number']
                table = record['result']['table']
                sys_id = record['result']['sys_id']

            attachment_api_url = f'{api_url}/attachment/file?table={table}&table_sys_id={sys_id}'
            for attachment in attachment_file_list:
                print(f"------------------- Upload File {attachment['fileName']} - {attachment['contentType']} ----------------------")
                attachment_api_data = {
                    'attachments': {
                        "fileName": attachment['fileName'],
                        "contentType": attachment['contentType'],
                        "content": attachment['content']
                    }
                }
                print(f"------------------------- uploading attachment {attachment['fileName']} -------------------------")

                # Do the HTTP request
                attachment_response = requests.post(attachment_api_url, auth=(user, pwd), headers=headers, data=json.dumps(attachment_api_data), verify=verify_ssl)
                # Check for HTTP codes other than 200
                attachment_response_json = attachment_response.json()
                response_dict.setdefault('attachment_response', []).append(attachment_response_json)
                print(attachment_response.status_code)

                if attachment_response.status_code not in [200, 201]:
                    pprint(attachment_response_json)
                    is_submit = False
                    print(f'Attachment upload failed for {company_code} {cost_center} {target_folder_name}')
                else:
                    print(f"Attachment uploaded for {attachment['fileName']}")
                    pprint(attachment_response_json)

        print(f'-------------------  upload result for {company_code} {cost_center} {target_folder_name} -------------------')
        print(is_submit, ssf_number)
        return is_submit, ssf_number, response_dict
    except:
        print(traceback.format_exc())
        is_submit = False
        ssf_number = ''
        return is_submit, ssf_number, {}


def submit_b2p_fund_transfer_ticket(api_url, api_username, api_password, requested_for, short_description, request_table, company_code, department,
                                    attachment_file_path_list=None, verify_ssl=True):
    """This function is used to submit fund transfer ticket

    Args:
        api_url(str): This is the API URL for the B2P Fund Transfer. e.g. https://gbs.bosch.com/api/robgh/esm_finance_catalog_api/sys_id/7235d7d61b5de114c8ba777c8b4bcb86
        api_username(str): This is the API username for the B2P Fund Transfer
        api_password(str): This is the API password for the B2P Fund Transfer
        requested_for(str): The requested for user id
        short_description(str): The short description for esm ticket
        request_table(str): The request table in html format
        company_code(str): The company code
        department(str): The department
        attachment_file_path_list(list): The attachment file path list
        verify_ssl(bool|str): This is the flag to verify SSL for the ESM API request
    """
    check_result = True
    error_message = ""
    magic_tool = magic.Magic(mime=True)

    try:
        attachment_file_path_list = attachment_file_path_list if attachment_file_path_list is not None else []
        attachment_file_obj_list = []

        if attachment_file_path_list:
            for attachment_file_path in attachment_file_path_list:
                with open(attachment_file_path, "rb") as f:
                    file_content = f.read()
                    file_base64 = base64.b64encode(file_content).decode("utf-8")

                file_name = os.path.basename(attachment_file_path)
                _, file_ext = os.path.splitext(file_name)
                content_type = MIME_TYPE_MAP.get(
                    file_ext.upper(),
                    magic_tool.from_file(attachment_file_path),
                )
                attachment_file_obj_list.append(
                    {
                        "fileName": file_name,
                        "contentType": content_type,
                        "content": file_base64,
                    }
                )
        # Set proper headers
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        ticket_data = {
            "variables": {
                "u_requested_for": requested_for,
                "short_description": short_description,
                "request": request_table,
                "u_ssf_company_code": company_code,
                "u_ssf_category": "B2R: Book To Report - Preparing & Recording",
                "u_ssf_subcategory": "Fund Transfer",
                "u_department": department,
                "u_substitute": "",
            },
            "attachments": attachment_file_obj_list,
        }

        # Do the HTTP request
        response = requests.post(api_url, auth=(api_username, api_password), headers=headers, data=json.dumps(ticket_data), verify=verify_ssl)
        if response.status_code in [200, 201]:
            res_data = response.json()
            return check_result, error_message, res_data
        else:
            check_result = False
            error_message = f"ESM工单提交失败，状态码：{response.status_code}，返回信息：{response.text}"
            return check_result, error_message, None
    except:
        print(traceback.format_exc())
        check_result = False
        error_message = "ESM工单提交异常，请检查网络或系统配置"
        return check_result, error_message, None

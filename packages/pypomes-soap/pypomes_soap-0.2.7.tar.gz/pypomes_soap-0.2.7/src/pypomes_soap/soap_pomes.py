import ast
import json
import requests
from collections.abc import Callable
from lxml import etree
from pathlib import Path
from pypomes_core import dict_jsonify, xml_to_dict
from typing import Any
from zeep import Client


def soap_build_envelope(ws_url: str,
                        service: str,
                        payload: dict,
                        filepath: Path = None) -> bytes:
    """
    Construct and return the SOAP envelope for a given service.

    This envelope does not contain the *headers*.

    :param ws_url: the request URL
    :param payload: the data to be sent
    :param service: the name of the service
    :param filepath: path to store the soap envelope
    :return: the envelope for the SOAP request, without the headers
    """
    # obtain the client
    zeep_client: Client = Client(wsdl=ws_url)
    # obtain the XML envelope
    root = zeep_client.create_message(service=zeep_client.service,
                                      operation_name=service,
                                      **payload)
    # noinspection PyTypeChecker
    result: bytes = etree.tostring(element_or_tree=root,
                                   pretty_print=True)
    if filepath:
        # save the envelope to file
        with filepath.open(mode="wb") as f:
            f.write(result)

    return result


def soap_post(ws_url: str,
              soap_envelope: bytes,
              extra_headers: dict = None,
              filepath: Path = None,
              timeout: int = None) -> bytes:
    """
    Forward the SOAP request, and return the received response.

    :param ws_url: the request URL
    :param soap_envelope: the SOAP envelope
    :param extra_headers: additional headers
    :param filepath: path to store the response to the request
    :param timeout: timeout, in seconds (defaults to HTTP_POST_TIMEOUT - use None to omit)
    :return: the response to the SOAP request
    """
    # constrói o cabeçalho do envelope SOAP
    headers: dict = {"SOAPAction": '""',
                     "content-type": "application/soap+xml; charset=utf-8"}
    if extra_headers:
        # acknowledge the additional headers
        headers.update(extra_headers)

    # send the request
    response: requests.Response = requests.post(url=ws_url,
                                                data=soap_envelope,
                                                headers=headers,
                                                timeout=timeout)
    result: bytes = response.content

    if filepath:
        # save the response to file
        with filepath.open(mode="wb") as f:
            f.write(result)

    return result


def soap_post_zeep(zeep_service: Callable,
                   payload: dict,
                   filepath: Path = None) -> dict:
    """
    Forward the SOAP request using the *zeep* package, and return the received response.

    :param zeep_service: the reference service
    :param payload: the data to be sent
    :param filepath: path to store the JSON corresponding to the returned response
    :return: the response to the SOAP request
    """
    # invoke the service
    # ('response' is a dict subclass - defined in the wsdl as the return to 'zeep_service')
    response: Any = zeep_service(**payload)

    # convert the returned content to 'dict' and prepare it for dumping in JSON
    result: dict = ast.literal_eval(str(response))
    dict_jsonify(source=result)

    if filepath:
        # save the response to file
        with filepath.open(mode="w") as f:
            f.write(json.dumps(obj=result,
                               ensure_ascii=False))

    return result


def soap_get_dict(soap_response: bytes,
                  xml_path: Path = None,
                  json_path: Path = None) -> dict:
    """
    Retrieve the *dict* object containing the data returned by the SOAP request.

    This object is returned ready to be downloaded in JSON format.

    :param soap_response: the content returned by the SOAP request
    :param xml_path: path to store the XML correspondinge to the returned response
    :param json_path: path to store the JSON correspondinge to the returned response
    :return: the object with the response data to the SOAP request
    """
    # restrict the returned content to the content of 'soap:Body'
    pos_1: int = soap_response.find(b"<soap:Body>") + 11
    pos_2: int = soap_response.find(b"</soap:Body>", pos_1)
    content: bytes = soap_response[pos_1:pos_2]

    if xml_path:
        # save the returned XML content to file
        with xml_path.open(mode="wb") as f:
            f.write(content)

    # convert the returned XML content to 'dict' and prepare it for dumping in JSON
    result: dict = xml_to_dict(file_data=content)
    dict_jsonify(source=result)

    if json_path:
        # save the response to file
        with json_path.open(mode="w") as f:
            f.write(json.dumps(obj=result,
                               ensure_ascii=False))

    return result


def soap_get_cids(soap_response: bytes) -> list[bytes]:
    """
    Retrieve the *cids* in *soap_response*, indicative of attachments returned in the *MTOM* standard.

    The standard *Message Transmission Optimization Mechanism* defines *cids* (*Content-IDs*)
    in *tags* type
        - <xop:Include xmlns:xop="http://www.w3.org/2004/08/xop/include" href="cid:<uuid4>-<NN>@<web-address>"/>

    where the variables have the meanings:
        - *<uuid4*>: uma *UUID* versão 4
        - *<NN*>: um inteiro de dois dígitos
        - *<web-address*>: o endereço web associado

    The *cids* are returned as *<uuid4>-<NN>@<web-address*.

    :param soap_response: the content returned by the SOAP request
    :return: the list of 'content ids' found, which may be empty
    """
    # initialize the return variable
    result: list[bytes] = []

    prefix: bytes = b'href="cid:'
    pos_1: int = soap_response.find(prefix)
    while pos_1 > 0:
        pos_1 += len(prefix)
        pos_2: int = soap_response.find(b'"', pos_1)
        result.append(soap_response[pos_1:pos_2])
        pos_1 = soap_response.find(prefix, pos_1)

    return result


def soap_get_attachment(soap_response: bytes,
                        cid: bytes,
                        filepath: Path = None) -> bytes:
    """
    Retrieve the attachment contained in the *response* to the *SOAP* request, in the *MTOM* pattern.

    In this standard (*Message Transmission Optimization Mechanism*), the attachment is identified
    by its *cid* (*Content-ID*).

    :param soap_response: the content returned by the SOAP request
    :param cid: the attachement identification
    :param filepath: path to store the JSON corresponding to the returned attachment
    :return: the reference attachment, or 'None' if it was not found
    """
    # initialize the return variable
    result: bytes | None = None

    # locate the start of the attachment
    mark: bytes = b"Content-ID: <" + cid + b">"
    pos_1 = soap_response.find(mark)

    if pos_1 > 0:
        pos_1 += len(mark)
        # skip control chars (CR, LF, and others)
        blank: int = b" "[0]
        while soap_response[pos_1] < blank:
            pos_1 += 1

        # obtain the separator
        pos_2: int = soap_response.find(b"--uuid:")

        separator: bytes = soap_response[pos_2:pos_2+45]  # 45 = 2 + length of uuid4 + 7

        # locate the end of the attachment
        pos_2 = soap_response.find(separator, pos_1)

        # retrieve the attachment
        result: bytes = soap_response[pos_1:pos_2]

        if filepath:
            # save the attachment to file
            with filepath.open("wb") as f:
                f.write(result)

    return result

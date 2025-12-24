*&---------------------------------------------------------------------*
*& Class ZAKIR_SERIAL_SERVICE_CLASS
*&---------------------------------------------------------------------*
*& This class provides methods for calling the opscalesrv software.
*& When opscalesrv is called, it reads the serial port specified on the computer it's running on and returns a value.
*& This class parses the incoming value and provides it as a method result.
*& 
*& OpScaleSrv Response Types:
*& 1. Success Response: {"value": "25.5", "msg": "Temperature reading successful", "mode": "read", "result": "OK"}
*& 2. Error Response: {"value": "-1", "msg": "Serial port error", "mode": "read", "result": "FAIL"}
*& 3. Test Mode Response: {"value": "0", "msg": "hello world", "mode": "test", "result": "OK"} (only in test_connection)
*&
*& You can install opscalesrv on a computer with Python installed:
*& using pip install opscalesrv or pip3 install opscalesrv.
*& For detailed information, please visit:
*& https://pypi.org/project/opscalesrv
*& or
*& https://github.com/altaykirecci/opscalesrv.
*& Author: Altay Kireççi (c)(p)2025-09
*&---------------------------------------------------------------------*

CLASS ZAKIR_SERIAL_SERVICE_CLASS DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC .

  PUBLIC SECTION.
    TYPES: BEGIN OF ty_message,
             value  TYPE string,
             msg    TYPE string,
             mode   TYPE string,
             result TYPE string,
             plate  TYPE string,
           END OF ty_message.

    TYPES: BEGIN OF ty_response,
             message   TYPE ty_message,
             timestamp TYPE string,
             method    TYPE string,
             path      TYPE string,
             client_ip TYPE string,
             client_port TYPE string,
           END OF ty_response.

    TYPES: BEGIN OF ty_serial_result,
             success     TYPE abap_bool,
             value       TYPE string,
             message     TYPE string,
             mode        TYPE string,
             result      TYPE string,
             plate       TYPE string,
             timestamp   TYPE string,
             error_text  TYPE string,
           END OF ty_serial_result.

    CLASS-METHODS: call_serial_service
      IMPORTING
        iv_host        TYPE string 
        iv_port        TYPE string DEFAULT '7373'
        iv_path        TYPE string DEFAULT '/'
        iv_timeout     TYPE i DEFAULT 10
      RETURNING
        VALUE(rs_result) TYPE ty_serial_result
      EXCEPTIONS
        connection_error
        timeout_error
        parse_error.
    " Calls opscalesrv service and returns full response data
    " Supports Success and Error response types
    " Returns rs_result-success = false for FAIL responses (no exception)

    CLASS-METHODS: get_serial_value
      IMPORTING
        iv_host        TYPE string 
        iv_port        TYPE string DEFAULT '7373'
        iv_path        TYPE string DEFAULT '/'
        iv_timeout     TYPE i DEFAULT 10
      RETURNING
        VALUE(rv_value) TYPE string
      EXCEPTIONS
        connection_error
        timeout_error
        parse_error.
    " Returns only the serial value from response
    " Validates response type and value before returning
    " Returns empty string for Error Response (result: "FAIL") - no exception

    CLASS-METHODS: test_connection
      IMPORTING
        iv_host        TYPE string 
        iv_port        TYPE string DEFAULT '7373'
        iv_timeout     TYPE i DEFAULT 5
      RETURNING
        VALUE(rv_success) TYPE abap_bool
      EXCEPTIONS
        connection_error
        timeout_error
        parse_error.
    " Tests connection by requesting Test Mode Response
    " Validates response: result="OK", mode="test", value="0"
    " Returns true only if all validations pass

  PRIVATE SECTION.
    CLASS-METHODS: create_http_client
      IMPORTING
        iv_host        TYPE string
        iv_port        TYPE string
        iv_timeout     TYPE i
      RETURNING
        VALUE(ro_client) TYPE REF TO if_http_client
      EXCEPTIONS
        connection_error
        timeout_error
        parse_error.

    CLASS-METHODS: parse_json_response
      IMPORTING
        iv_json        TYPE string
      RETURNING
        VALUE(rs_response) TYPE ty_response
      EXCEPTIONS
        connection_error
        timeout_error
        parse_error.

    CLASS-METHODS: build_url
      IMPORTING
        iv_host        TYPE string
        iv_port        TYPE string
        iv_path        TYPE string DEFAULT '/'
        iv_test_mode   TYPE abap_bool DEFAULT abap_false
      RETURNING
        VALUE(rv_url) TYPE string.

ENDCLASS.

CLASS ZAKIR_SERIAL_SERVICE_CLASS IMPLEMENTATION.

  METHOD call_serial_service.
    DATA: lo_http_client TYPE REF TO if_http_client,
          lv_url         TYPE string,
          lv_response    TYPE string,
          lv_status_code TYPE i,
          lv_reason      TYPE string,
          ls_response    TYPE ty_response.

    " Initialize result
    CLEAR rs_result.

    " Build URL - Normal mode (no test parameter)
    lv_url = build_url( iv_host = iv_host iv_port = iv_port iv_path = iv_path iv_test_mode = abap_false ).

    " Create HTTP client
    TRY.
        lo_http_client = create_http_client(
          iv_host = iv_host
          iv_port = iv_port
          iv_timeout = iv_timeout
        ).
      CATCH cx_sy_conversion_no_number.
        rs_result-success = abap_false.
        rs_result-error_text = 'HTTP client creation failed'.
        RAISE connection_error.
    ENDTRY.

    " Set request URI
    lo_http_client->request->set_method( if_http_request=>co_request_method_get ).
    lo_http_client->request->set_header_field( name = 'Content-Type' value = 'application/json' ).

    " Send request
    TRY.
        lo_http_client->send( ).
        lo_http_client->receive( ).
      CATCH cx_sy_conversion_no_number.
        rs_result-success = abap_false.
        rs_result-error_text = 'HTTP request failed'.
        RAISE connection_error.
    ENDTRY.

    " Get response
    lo_http_client->response->get_status( IMPORTING code = lv_status_code reason = lv_reason ).
    lv_response = lo_http_client->response->get_cdata( ).

    " Check status code
    IF lv_status_code <> 200.
      rs_result-success = abap_false.
      rs_result-error_text = |HTTP Error { lv_status_code }: { lv_reason }|.
        RAISE connection_error.
    ENDIF.

    " Parse JSON response
    TRY.
        ls_response = parse_json_response( iv_json = lv_response ).
      CATCH cx_sy_conversion_no_number.
        rs_result-success = abap_false.
        rs_result-error_text = 'HTTP client creation failed'.
        RAISE connection_error.
    ENDTRY.

    " Check response result based on response type
    IF ls_response-message-result = 'FAIL'.
      " Error Response: Serial port hatası
      rs_result-success = abap_false.
      rs_result-value = ls_response-message-value.  " "-1"
      rs_result-message = ls_response-message-msg.
      rs_result-mode = ls_response-message-mode.    " "read"
      rs_result-result = ls_response-message-result. " "FAIL"
      rs_result-plate = ls_response-message-plate.
      rs_result-timestamp = ls_response-timestamp.
      rs_result-error_text = ls_response-message-msg.
      " Exception fırlatmak yerine result'ı doldur ve method'dan çık
      " Caller'da rs_result-success kontrol edilecek
    ELSEIF ls_response-message-result = 'OK'.
      " Success Response: Başarılı serial okuma
      rs_result-success = abap_true.
      rs_result-value = ls_response-message-value.
      rs_result-message = ls_response-message-msg.
      rs_result-mode = ls_response-message-mode.    " "read"
      rs_result-result = ls_response-message-result. " "OK"
      rs_result-plate = ls_response-message-plate.
      rs_result-timestamp = ls_response-timestamp.
      rs_result-error_text = ''.
    ELSE.
      " Unknown response type
      rs_result-success = abap_false.
      rs_result-value = '-1'.
      rs_result-message = 'Unknown response type'.
      rs_result-mode = 'unknown'.
      rs_result-result = 'UNKNOWN'.
      rs_result-timestamp = ls_response-timestamp.
      rs_result-error_text = |Unknown response result: { ls_response-message-result }|.
      " Exception fırlatmak yerine result'ı doldur ve method'dan çık
      " Caller'da rs_result-success kontrol edilecek
    ENDIF.

    " Close HTTP client
    lo_http_client->close( ).

  ENDMETHOD.

  METHOD get_serial_value.
    DATA: ls_result TYPE ty_serial_result.

    " Call serial service
    TRY.
        ls_result = call_serial_service(
          iv_host = iv_host
          iv_port = iv_port
          iv_path = iv_path
          iv_timeout = iv_timeout
        ).
      CATCH cx_sy_conversion_no_number.
        RAISE connection_error.
    ENDTRY.

    " Check if result is successful
    IF ls_result-success = abap_false.
      " Exception fırlatmak yerine boş string döndür
      rv_value = ''.
      RETURN.
    ENDIF.

    " Validate response type and value
    IF ls_result-result = 'OK' AND ls_result-value IS NOT INITIAL.
      " Success Response
      rv_value = ls_result-value.
    ELSEIF ls_result-result = 'FAIL' AND ls_result-value = '-1'.
      " Error Response - Serial port hatası
      " Exception fırlatmak yerine boş string döndür
      rv_value = ''.
    ELSE.
      " Unknown or invalid response
      " Exception fırlatmak yerine boş string döndür
      rv_value = ''.
    ENDIF.

  ENDMETHOD.

  METHOD test_connection.
    DATA: lo_http_client TYPE REF TO if_http_client,
          lv_url         TYPE string,
          lv_status_code TYPE i,
          lv_reason      TYPE string,
          lv_response    TYPE string,
          ls_response    TYPE ty_response.

    " Initialize result
    rv_success = abap_false.

    " Build URL - Test mode kullanarak bağlantıyı test et
    lv_url = build_url( iv_host = iv_host iv_port = iv_port iv_test_mode = abap_true ).

    " Create HTTP client
    TRY.
        lo_http_client = create_http_client(
          iv_host = iv_host
          iv_port = iv_port
          iv_timeout = iv_timeout
        ).
      CATCH cx_sy_conversion_no_number.
        RAISE connection_error.
    ENDTRY.

    " Set request URI
    lo_http_client->request->set_method( if_http_request=>co_request_method_get ).
    lo_http_client->request->set_header_field( name = 'Content-Type' value = 'application/json' ).

    " Send request
    TRY.
        lo_http_client->send( ).
        lo_http_client->receive( ).
      CATCH cx_sy_conversion_no_number.
        RAISE connection_error.
    ENDTRY.

    " Get response
    lo_http_client->response->get_status( IMPORTING code = lv_status_code reason = lv_reason ).
    lv_response = lo_http_client->response->get_cdata( ).

    " Check status code
    IF lv_status_code = 200.
      " HTTP başarılı, şimdi response içeriğini kontrol et
      TRY.
          ls_response = parse_json_response( iv_json = lv_response ).
          
          " Test Mode Response bekliyoruz
          IF ls_response-message-result = 'OK' AND 
             ls_response-message-mode = 'test' AND
             ls_response-message-value = '0'.
            rv_success = abap_true.
          ELSE.
            " Beklenmeyen response
            rv_success = abap_false.
          ENDIF.
        CATCH cx_sy_conversion_no_number.
          " JSON parse hatası
          rv_success = abap_false.
      ENDTRY.
    ELSE.
      " HTTP hatası
      rv_success = abap_false.
    ENDIF.

    " Close HTTP client
    lo_http_client->close( ).

  ENDMETHOD.

  METHOD create_http_client.
    DATA: lv_url TYPE string.

    " Build URL
    lv_url = |http://{ iv_host }:{ iv_port }/|.

    " Create HTTP client
    TRY.
        cl_http_client=>create_by_url(
          EXPORTING
            url                = lv_url
            ssl_id             = 'ANONYM'
          IMPORTING
            client             = ro_client
        ).
      CATCH cx_sy_conversion_no_number.
        RAISE connection_error.
    ENDTRY.

    " Timeout is handled by the HTTP client creation

  ENDMETHOD.

  METHOD parse_json_response.
    DATA: lo_json TYPE REF TO /ui2/cl_json.

    " Create JSON parser
    CREATE OBJECT lo_json.

    " Parse JSON
    TRY.
        lo_json->deserialize(
          EXPORTING
            json = iv_json
          CHANGING
            data = rs_response
        ).
      CATCH cx_sy_conversion_no_number.
        RAISE parse_error.
    ENDTRY.

  ENDMETHOD.

  METHOD build_url.
    DATA: lv_clean_path TYPE string.
    
    " Clean path - ensure it starts with /
    lv_clean_path = iv_path.
    IF lv_clean_path(1) <> '/'.
      lv_clean_path = |/{ lv_clean_path }|.
    ENDIF.
    
    IF iv_test_mode = abap_true.
      rv_url = |http://{ iv_host }:{ iv_port }{ lv_clean_path }?test=1|.
    ELSE.
      rv_url = |http://{ iv_host }:{ iv_port }{ lv_clean_path }|.
    ENDIF.
  ENDMETHOD.

ENDCLASS.

*&---------------------------------------------------------------------*
*& Example Usage:
*&---------------------------------------------------------------------*
*& DATA: ls_result TYPE ZAKIR_SERIAL_SERVICE_CLASS=>ty_serial_result,
*&       lv_value  TYPE string.
*&
*& " 1. Call serial service and get full result (Success/Error response types)
*& TRY.
*&     ls_result = ZAKIR_SERIAL_SERVICE_CLASS=>call_serial_service(
*&       iv_host = '192.168.1.100'
*&       iv_port = '7373'
*&       iv_path = '/entrance'  " or '/exit' or '/'
*&       iv_timeout = 10
*&     ).
*&     IF ls_result-success = abap_true.
*&       WRITE: / 'Value:', ls_result-value,
*&                / 'Message:', ls_result-message,
*&                / 'Mode:', ls_result-mode,  " "read"
*&                / 'Result:', ls_result-result,  " "OK"
*&                / 'Plate:', ls_result-plate.  " "ENTRANCE", "EXIT", "NO_DIRECTIONS", or "NO_PLATE"
*&       " Check if plate is available
*&       IF ls_result-plate <> 'NO_PLATE'.
*&         WRITE: / 'Plate detected:', ls_result-plate.
*&       ENDIF.
*&     ELSE.
*&       WRITE: / 'Error Response - Value:', ls_result-value,  " "-1"
*&            / 'Error Message:', ls_result-error_text,
*&            / 'Mode:', ls_result-mode,  " "read"
*&            / 'Result:', ls_result-result.  " "FAIL"
*&     ENDIF.
*&   CATCH ZAKIR_SERIAL_SERVICE_CLASS=>connection_error.
*&     WRITE: / 'Connection error occurred'.
*&   CATCH ZAKIR_SERIAL_SERVICE_CLASS=>timeout_error.
*&     WRITE: / 'Timeout error occurred'.
*&   CATCH ZAKIR_SERIAL_SERVICE_CLASS=>parse_error.
*&     WRITE: / 'Parse error occurred'.
*& ENDTRY.
*&
*& " 2. Get only the value (validates response type)
*& TRY.
*&     lv_value = ZAKIR_SERIAL_SERVICE_CLASS=>get_serial_value(
*&       iv_host = '192.168.1.100'
*&       iv_port = '7373'
*&       iv_path = '/entrance'  " or '/exit' or '/'
*&     ).
*&     IF lv_value IS NOT INITIAL.
*&       WRITE: / 'Serial Value:', lv_value.
*&     ELSE.
*&       WRITE: / 'No value returned - check serial port connection'.
*&     ENDIF.
*&   CATCH ZAKIR_SERIAL_SERVICE_CLASS=>connection_error.
*&     WRITE: / 'Connection error occurred'.
*&   CATCH ZAKIR_SERIAL_SERVICE_CLASS=>timeout_error.
*&     WRITE: / 'Timeout error occurred'.
*&   CATCH ZAKIR_SERIAL_SERVICE_CLASS=>parse_error.
*&     WRITE: / 'Parse error occurred'.
*& ENDTRY.
*&
*& " 3. Test connection (validates Test Mode Response)
*& TRY.
*&     IF ZAKIR_SERIAL_SERVICE_CLASS=>test_connection(
*&       iv_host = '192.168.1.100'
*&       iv_port = '7373'
*&     ) = abap_true.
*&       WRITE: / 'Connection successful - service is running'.
*&     ELSE.
*&       WRITE: / 'Connection failed - service not responding'.
*&     ENDIF.
*&   CATCH ZAKIR_SERIAL_SERVICE_CLASS=>connection_error.
*&     WRITE: / 'Connection error occurred'.
*&   CATCH ZAKIR_SERIAL_SERVICE_CLASS=>timeout_error.
*&     WRITE: / 'Timeout error occurred'.
*& ENDTRY.
*&---------------------------------------------------------------------*

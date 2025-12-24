*&---------------------------------------------------------------------*
*& Report ZAKIR_SERIAL_CLASS_TEST 
*&---------------------------------------------------------------------*
*& This program demonstrates how to use the ZAKIR_SERIAL_SERVICE_CLASS class
*& to call the opscalesrv software and retrieve serial port data.
*& 
*& The class provides three main methods:
*& 1. call_serial_service - Get full response with all details (Success/Error)
*& 2. get_serial_value - Get only the serial value
*& 3. test_connection - Test if server is reachable (uses Test Mode)
*&
*& Response Types:
*& - Success Response: {"value": "25.5", "mode": "read", "result": "OK"}
*& - Error Response: {"value": "-1", "mode": "read", "result": "FAIL"}
*& - Test Mode Response: {"value": "0", "mode": "test", "result": "OK"} (test_connection only)
*&
*& You can install opscalesrv on a computer with Python installed:
*& using pip install opscalesrv or pip3 install opscalesrv.
*& For detailed information, please visit:
*& https://pypi.org/project/opscalesrv
*& or
*& https://github.com/altaykirecci/opscalesrv.
*&
*& Author: Altay Kireççi (c)(p)2025-09
*&---------------------------------------------------------------------*

REPORT zakir_serial_class_test.

* Selection screen parameters
SELECTION-SCREEN BEGIN OF BLOCK b1 WITH FRAME TITLE TEXT-001.
PARAMETERS: p_host TYPE string DEFAULT 'localhost' OBLIGATORY,
            p_port TYPE string DEFAULT '7373' OBLIGATORY,
            p_time TYPE i DEFAULT 10 OBLIGATORY.
SELECTION-SCREEN END OF BLOCK b1.

SELECTION-SCREEN BEGIN OF BLOCK b2 WITH FRAME TITLE TEXT-002.
PARAMETERS: p_full AS CHECKBOX DEFAULT 'X',
            p_value AS CHECKBOX,
            p_test AS CHECKBOX.
SELECTION-SCREEN END OF BLOCK b2.

* Text elements
SELECTION-SCREEN BEGIN OF BLOCK b3 WITH FRAME TITLE TEXT-003.
SELECTION-SCREEN COMMENT /1(70) TEXT-004.
SELECTION-SCREEN COMMENT /1(70) TEXT-005.
SELECTION-SCREEN COMMENT /1(70) TEXT-006.
SELECTION-SCREEN END OF BLOCK b3.

* Text symbols (to be defined in SE80)
* TEXT-001: Connection Parameters
* TEXT-002: Test Options
* TEXT-003: Response Types
* TEXT-004: Success Response: {"value": "25.5", "mode": "read", "result": "OK"}
* TEXT-005: Error Response: {"value": "-1", "mode": "read", "result": "FAIL"}
* TEXT-006: Test Mode Response: {"value": "0", "mode": "test", "result": "OK"} (test_connection only)
* TEXT-007: Note: Only GET method is supported, POST requests return 405 Method Not Allowed

* Data declarations
DATA: ls_result TYPE ZAKIR_SERIAL_SERVICE_CLASS=>ty_serial_result,
      lv_value  TYPE string,
      lv_success TYPE abap_bool.

* Text symbols
SELECTION-SCREEN BEGIN OF BLOCK b4 WITH FRAME.
SELECTION-SCREEN COMMENT /1(70) TEXT-007.
SELECTION-SCREEN END OF BLOCK b4.

* Main program
START-OF-SELECTION.
  PERFORM main.

*&---------------------------------------------------------------------*
*& Form MAIN
*&---------------------------------------------------------------------*
FORM main.
  WRITE: / 'OpScaleSrv Method Test Program',
         / '==============================',
         / 'Testing ZAKIR_SERIAL_SERVICE_CLASS methods',
         / 'Only GET method is supported, POST returns 405',
         /.

  " Test connection first (uses Test Mode Response)
  IF p_test = 'X'.
    PERFORM test_connection.
  ENDIF.

  " Get full result (Success/Error Response)
  IF p_full = 'X'.
    PERFORM get_full_result.
  ENDIF.

  " Get only value (validates response type)
  IF p_value = 'X'.
    PERFORM get_serial_value.
  ENDIF.

  WRITE: / 'Test completed successfully!'.
ENDFORM.

*&---------------------------------------------------------------------*
*& Form TEST_CONNECTION
*&---------------------------------------------------------------------*
FORM test_connection.
  WRITE: / 'Testing connection...'.

  TRY.
      lv_success = ZAKIR_SERIAL_SERVICE_CLASS=>test_connection(
        iv_host = p_host
        iv_port = p_port
        iv_timeout = p_time
      ).
      
      IF lv_success = abap_true.
        WRITE: / '✅ Connection successful! Server is running and responding.'.
      ELSE.
        WRITE: / '❌ Connection failed! Server not responding or not reachable.'.
      ENDIF.
      
    CATCH cx_sy_conversion_no_number.
      WRITE: / '❌ HTTP Error occurred'.
  ENDTRY.
  
  WRITE: /.
ENDFORM.

*&---------------------------------------------------------------------*
*& Form GET_FULL_RESULT
*&---------------------------------------------------------------------*
FORM get_full_result.
  WRITE: / 'Getting full result...'.

  TRY.
      ls_result = ZAKIR_SERIAL_SERVICE_CLASS=>call_serial_service(
        iv_host = p_host
        iv_port = p_port
        iv_timeout = p_time
      ).
      
      IF ls_result-success = abap_true.
        WRITE: / '✅ Success Response - Data retrieved successfully!',
               / 'Value:', ls_result-value,
               / 'Message:', ls_result-message,
               / 'Mode:', ls_result-mode,  " "read"
               / 'Result:', ls_result-result,  " "OK"
               / 'Timestamp:', ls_result-timestamp.
      ELSE.
        WRITE: / '❌ Error Response - Serial port error occurred:',
               / 'Value:', ls_result-value,  " "-1"
               / 'Error Message:', ls_result-error_text,
               / 'Mode:', ls_result-mode,  " "read"
               / 'Result:', ls_result-result.  " "FAIL"
      ENDIF.
      
    CATCH cx_sy_conversion_no_number.
      WRITE: / '❌ HTTP Error occurred'.
  ENDTRY.
  
  WRITE: /.
ENDFORM.

*&---------------------------------------------------------------------*
*& Form GET_SERIAL_VALUE
*&---------------------------------------------------------------------*
FORM get_serial_value.
  WRITE: / 'Getting serial value...'.

  TRY.
      lv_value = ZAKIR_SERIAL_SERVICE_CLASS=>get_serial_value(
        iv_host = p_host
        iv_port = p_port
        iv_timeout = p_time
      ).
      
      IF lv_value IS NOT INITIAL.
        WRITE: / '✅ Serial Value:', lv_value.
      ELSE.
        WRITE: / '❌ No value returned - check serial port connection.'.
      ENDIF.
      
    CATCH cx_sy_conversion_no_number.
      WRITE: / '❌ HTTP Error occurred'.
  ENDTRY.
  
  WRITE: /.
ENDFORM.

#include <Python.h>
#include "nell_scb_c.h"

// Helper to parse JSON string to Python dict
static PyObject* json_string_to_dict(const char* json_str) {
    if (!json_str) {
        Py_RETURN_NONE;
    }
    
    // Import json module
    PyObject* json_module = PyImport_ImportModule("json");
    if (!json_module) {
        return NULL;
    }
    
    // Get json.loads function
    PyObject* loads_func = PyObject_GetAttrString(json_module, "loads");
    Py_DECREF(json_module);
    if (!loads_func) {
        return NULL;
    }
    
    // Convert C string to Python string
    PyObject* py_str = PyUnicode_FromString(json_str);
    if (!py_str) {
        Py_DECREF(loads_func);
        return NULL;
    }
    
    // Call json.loads(json_str)
    PyObject* result = PyObject_CallFunctionObjArgs(loads_func, py_str, NULL);
    Py_DECREF(loads_func);
    Py_DECREF(py_str);
    
    return result;
}

static PyObject* scb_api_create_qr(PyObject* self, PyObject* args) {
    const char* config_id;
    float amount;
    const char* reference;
    const char* channel = "ecomm";
    
    if (!PyArg_ParseTuple(args, "sfs|s", &config_id, &amount, &reference, &channel)) {
        return NULL;
    }
    
    // Call C implementation
    char* json_result = scb_create_qr_impl(config_id, amount, reference, channel);
    if (json_result == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create QR code");
        return NULL;
    }
    
    PyObject* result = PyUnicode_FromString(json_result);
    scb_free(json_result);
    
    return result;
}

static PyObject* scb_api_check_payment(PyObject* self, PyObject* args) {
    const char* reference;
    
    if (!PyArg_ParseTuple(args, "s", &reference)) {
        return NULL;
    }
    
    // Call C implementation
    char* json_result = scb_check_payment_impl(reference);
    if (json_result == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to check payment status");
        return NULL;
    }
    
    PyObject* result = PyUnicode_FromString(json_result);
    scb_free(json_result);
    
    return result;
}

static PyObject* scb_api_refresh_token(PyObject* self, PyObject* args) {
    const char* config_id;
    
    if (!PyArg_ParseTuple(args, "s", &config_id)) {
        return NULL;
    }
    
    // Call C implementation
    char* json_result = scb_refresh_token_by_config_id(config_id);
    if (json_result == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "C library returned NULL - internal error");
        return NULL;
    }
    
    PyObject* result = json_string_to_dict(json_result);
    scb_free(json_result);
    
    return result;
}

static PyObject* scb_api_create_qr_full(PyObject* self, PyObject* args) {
    const char* api_key;
    const char* access_token;
    const char* qr_create_url;
    const char* biller_id;
    float amount;
    const char* ref1;
    const char* ref2;
    const char* ref3;
    
    if (!PyArg_ParseTuple(args, "ssssfss|s", 
            &api_key, &access_token, &qr_create_url, &biller_id,
            &amount, &ref1, &ref2, &ref3)) {
        return NULL;
    }
    
    // Call C implementation
    char* json_result = scb_create_qr_full(
        api_key, access_token, qr_create_url, biller_id,
        amount, ref1, ref2, ref3
    );
    if (json_result == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "C library returned NULL - internal error");
        return NULL;
    }
    
    PyObject* result = json_string_to_dict(json_result);
    scb_free(json_result);
    
    return result;
}

static PyObject* scb_api_create_qr_by_bank(PyObject* self, PyObject* args) {
    const char* bank_account_id;
    float amount;
    const char* ref1;
    const char* ref2;
    const char* ref3 = "SCB";
    
    if (!PyArg_ParseTuple(args, "sfss|s", 
            &bank_account_id, &amount, &ref1, &ref2, &ref3)) {
        return NULL;
    }
    
    // Call C implementation
    char* json_result = scb_create_qr_by_bank_account(
        bank_account_id, amount, ref1, ref2, ref3
    );
    if (json_result == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "C library returned NULL - internal error");
        return NULL;
    }
    
    // Parse JSON to Python dict
    PyObject* result = json_string_to_dict(json_result);
    scb_free(json_result);
    
    return result;
}

static PyObject* scb_api_payment_inquiry(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* config_id;
    const char* transaction_ref = NULL;
    const char* biller_id = NULL;
    const char* reference1 = NULL;
    const char* reference2 = NULL;
    const char* amount = NULL;
    const char* transaction_date = NULL;
    
    static char* kwlist[] = {"config_id", "transaction_ref", "biller_id", 
                             "reference1", "reference2", "amount", 
                             "transaction_date", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|zzzzzz", kwlist,
            &config_id, &transaction_ref, &biller_id, &reference1, 
            &reference2, &amount, &transaction_date)) {
        return NULL;
    }
    
    // Call C implementation
    char* json_result = scb_payment_inquiry(
        config_id, transaction_ref, biller_id, reference1,
        reference2, amount, transaction_date
    );
    if (json_result == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "C library returned NULL - internal error");
        return NULL;
    }
    
    // Parse JSON to Python dict
    PyObject* result = json_string_to_dict(json_result);
    scb_free(json_result);
    
    return result;
}

static PyObject* scb_api_create_qr_for_invoice(PyObject* self, PyObject* args, PyObject* kwargs) {
    int invoice_id;
    int company_id;
    int config_id;
    const char* reference;
    float amount;
    const char* bank_account_id;
    
    static char* kwlist[] = {"invoice_id", "company_id", "config_id",
                             "reference", "amount", "bank_account_id", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "iiisfs", kwlist,
            &invoice_id, &company_id, &config_id, &reference, &amount, &bank_account_id)) {
        return NULL;
    }
    
    // Connect to database
    PGconn* conn = scb_db_connect(NULL);
    if (!conn) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to connect to database");
        return NULL;
    }
    
    // Call C implementation
    char* json_result = scb_create_qr_for_invoice(
        conn, invoice_id, company_id, config_id,
        reference, amount, bank_account_id
    );
    
    scb_db_close(conn);
    
    if (json_result == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "C library returned NULL - internal error");
        return NULL;
    }
    
    // Parse JSON to Python dict
    PyObject* result = json_string_to_dict(json_result);
    scb_free(json_result);
    
    return result;
}

static PyObject* internal_telemetry_init(PyObject* self, PyObject* args) {
    // Call C implementation (no arguments - fetches everything from database)
    int result = scb_telemetry_init();
    
    if (result) {
        Py_RETURN_TRUE;
    } else {
        Py_RETURN_FALSE;
    }
}

static PyMethodDef ScbMethods[] = {
    {"scb_api_create_qr", scb_api_create_qr, METH_VARARGS,
     "Create SCB QR code"},
    {"scb_api_create_qr_full", scb_api_create_qr_full, METH_VARARGS,
     "Create SCB QR code with full parameters"},
    {"scb_api_create_qr_by_bank", scb_api_create_qr_by_bank, METH_VARARGS,
     "Create SCB QR code using bank account ID (fetches config from database)"},
    {"scb_api_check_payment", scb_api_check_payment, METH_VARARGS,
     "Check SCB payment status"},
    {"scb_api_refresh_token", scb_api_refresh_token, METH_VARARGS,
     "Refresh SCB access token"},
    {"scb_api_payment_inquiry", (PyCFunction)scb_api_payment_inquiry, METH_VARARGS | METH_KEYWORDS,
     "Check SCB payment status via payment inquiry API"},
    {"create_qr_for_invoice", (PyCFunction)scb_api_create_qr_for_invoice, METH_VARARGS | METH_KEYWORDS,
     "Create QR for invoice with intent caching (returns cached QR if exists)"},
    {"_internal_telemetry_init", internal_telemetry_init, METH_NOARGS,
     "Internal: Initialize telemetry (auto-called on module import)"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef scbmodule = {
    PyModuleDef_HEAD_INIT,
    "_binding",
    "Nellika SCB C Extension",
    -1,
    ScbMethods
};

PyMODINIT_FUNC PyInit__binding(void) {
    return PyModule_Create(&scbmodule);
}

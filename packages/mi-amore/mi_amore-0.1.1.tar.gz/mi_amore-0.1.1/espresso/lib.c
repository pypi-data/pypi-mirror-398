#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdlib.h>
#include <string.h>

/* Espresso headers */
#include "espresso.h"

/*
 * Python-Wrapper für Espresso-Minimierung
 * Input: Liste von (bits_string, output_bit) tuples
 * Output: Liste der minimierten Cubes
 */

static void my_print(set_family_t *F, char *name)
{

    printf("%s\n", name);
    sf_bm_print(F);
    cprint(F);
    printf("-----\n");
}

typedef struct
{
    char *bits; /* "10101" oder "1010-" */
    int output; /* 0 oder 1 */
} cube_t;

static set_family_t *get_family_set(PyObject *cubes_py, pset pcube_container)
{
    Py_ssize_t n_cubes = PyList_Size(cubes_py);
    set_family_t *family_set = sf_new(n_cubes, cube.size);

    for (Py_ssize_t i = 0; i < n_cubes; i++)
    {
        set_clear(pcube_container, cube.size);
        PyObject *pcube_py = PyList_GetItem(cubes_py, i);
        Py_ssize_t n_cubes = PyList_Size(pcube_py);
        for (Py_ssize_t j = 0; j < n_cubes; j++)
        {
            PyObject *item = PyList_GetItem(pcube_py, j);
            int value = PyLong_AsLong(item);
            if (value == 1)
            {
                set_insert(pcube_container, j);
            }
            //
        }
        if (n_cubes > 0)
            family_set = sf_addset(family_set, pcube_container);
    }
    return family_set;
}

static PyObject *espresso_minimize(PyObject *self, PyObject *args)
{
    int nbinary;
    PyObject *mvars, *cubesf_py, *cubesd_py, *cubesr_py;
    set_family_t *F;
    set_family_t *D;
    set_family_t *R;
    int verbosity = 0;

    if (!PyArg_ParseTuple(args, "iOOOO|i", &nbinary, &mvars, &cubesf_py, &cubesd_py, &cubesr_py, &verbosity))
    {
        return NULL;
    }
    cube.num_binary_vars = nbinary;
    Py_ssize_t n_mvars = PyList_Size(mvars);
    cube.num_vars = n_mvars + nbinary; //
    cube.part_size = ALLOC(int, cube.num_vars);
    for (int i = 0; i < n_mvars; i++)
    {

        int m_size = PyLong_AsLong(PyList_GetItem(mvars, i));
        cube.part_size[nbinary + i] = m_size;
    }

    // cube.part_size[cube.num_vars - 1] = 1;
    // cube.part_size[cube.num_vars - 1] = 4;
    cube_setup();

    for (int i = 0; i < cube.num_vars; i++)
    {
        printf("%d", cube.part_size[i]);
    }

    Py_ssize_t n_cubes = PyList_Size(cubesf_py);

    F = get_family_set(cubesf_py, cube.temp[0]);
    my_print(F, "F vorher");

    //

    R = get_family_set(cubesr_py, cube.temp[2]);
    my_print(R, "R vorher");

    D = get_family_set(cubesd_py, cube.temp[1]);
    my_print(D, "D vorher");

    my_print(complement(cube2list(F, R)), "F  R diff");

    printf("nbinary: %d\n", nbinary);
    printf("n_cubes: %d\n", n_cubes);

    F = espresso(F, D, R);
    my_print(F, "F after");
    PyObject *result = PyList_New(1);
    return result;
}

static PyObject *espresso_minimize_old(PyObject *self, PyObject *args)
{
    PyObject *cubes_py;
    int verbosity = 0;
    set_family_t *F, *Fsave;
    set_family_t *D;
    set_family_t *R;
    register int var, i;

    if (!PyArg_ParseTuple(args, "O|i", &cubes_py, &verbosity))
    {
        return NULL;
    }

    /* Validiere Input ist List */
    if (!PyList_Check(cubes_py))
    {
        PyErr_SetString(PyExc_TypeError, "Expected list of tuples");
        return NULL;
    }

    Py_ssize_t n_cubes = PyList_Size(cubes_py);
    if (n_cubes == 0)
    {
        return PyList_New(0);
    }

    /* Parse Input-Cubes */
    cube_t *cubes = malloc(n_cubes * sizeof(cube_t));
    int n_vars = 0;

    for (Py_ssize_t i = 0; i < n_cubes; i++)
    {
        PyObject *item = PyList_GetItem(cubes_py, i);

        if (!PyTuple_Check(item) || PyTuple_Size(item) != 2)
        {
            PyErr_SetString(PyExc_TypeError, "Expected tuple (bits, output)");
            free(cubes);
            return NULL;
        }

        PyObject *bits_obj = PyTuple_GetItem(item, 0);
        PyObject *out_obj = PyTuple_GetItem(item, 1);

        /* Extract bit string */
        if (!PyUnicode_Check(bits_obj))
        {
            PyErr_SetString(PyExc_TypeError, "bits must be string");
            free(cubes);
            return NULL;
        }

        const char *bits_str = PyUnicode_AsUTF8(bits_obj);
        cubes[i].bits = malloc(strlen(bits_str) + 1);
        strcpy(cubes[i].bits, bits_str);

        if (n_vars == 0)
        {
            n_vars = strlen(bits_str);
        }

        /* Extract output */
        cubes[i].output = PyLong_AsLong(out_obj);
        if (PyErr_Occurred())
        {
            free(cubes);
            return NULL;
        }
    }

    cube.num_binary_vars = n_vars;
    cube.num_vars = n_vars + 1;
    cube.part_size = ALLOC(int, cube.num_vars);
    cube.part_size[cube.num_vars - 1] = 1;

    cube_setup();
    printf("cube size: %i\n", cube.size);
    printf("cube num_vars: %i\n", cube.num_vars);
    printf("cube num_binary_vars: %i\n", cube.num_binary_vars);

    F = sf_new(n_cubes, cube.size);

    pcube cf = cube.temp[0], cr = cube.temp[1], cd = cube.temp[2];
    set_clear(cf, cube.size);

    // for (var = 0; var < cube.num_binary_vars; var++)
    //{
    // }

    // cd = cube.temp[1];
    // cr = cube.temp[2];
    // cf = new_cube();

    i = 20;
    set_insert(cf, i);
    set_insert(cf, i + 2);
    set_insert(cf, i + 4);

    F = sf_addset(F, cf);
    // F = sf_addset(F, *cf);

    D = new_cover(0);

    R = complement(cube1list(F));

    my_print(F, "F bevore");
    my_print(R, "R");
    my_print(D, "D");

    F = espresso(F, D, R);
    my_print(F, "F after");

    printf("ende\n");

    /* === Espresso API aufrufen ===
     * Hier würdest du:
     * 1. cover_t* F erzeugen (on-set) von den cubes
     * 2. ggf. cover_t* D (don't-care set)
     * 3. espresso(F, D, R) aufrufen
     * 4. Ergebnis back zu Python
     */

    /* Pseudocode (echte Implementierung abhängig von Espresso-Version): */
    /*
    cover_t F = alloc_cover(n_cubes);
    for (int i = 0; i < n_cubes; i++) {
        if (cubes[i].output == 1) {
            cube_t cube = string_to_cube(cubes[i].bits);
            F = cv_insert(F, cube);
        }
    }

    pPLA PLA = (pPLA) malloc(sizeof(PLA_t));
    PLA->F = F;
    PLA->D = NULL;
    PLA->R = NULL;
    PLA->ninputs = n_vars;
    PLA->noutputs = 1;

    pPLA PLA_min = espresso(PLA);

    // Konvertiere Ergebnis zu Python-Liste
    */

    /* SIMPLIFIED: Für Demo, gib einfach Input zurück (ersetze mit echtem Espresso-Call) */
    PyObject *result = PyList_New(n_cubes);
    for (Py_ssize_t i = 0; i < n_cubes; i++)
    {
        PyObject *tuple = PyTuple_New(2);
        PyTuple_SetItem(tuple, 0, PyUnicode_FromString(cubes[i].bits));
        PyTuple_SetItem(tuple, 1, PyLong_FromLong(cubes[i].output));
        PyList_SetItem(result, i, tuple);
    }

    /* Cleanup */
    for (Py_ssize_t i = 0; i < n_cubes; i++)
    {
        free(cubes[i].bits);
    }
    free(cubes);

    return result;
}

/* Module Method Definition */
static PyMethodDef EspressoMethods[] = {
    {"minimize",
     espresso_minimize,
     METH_VARARGS,
     "Minimize Boolean function using Espresso\n"
     "minimize(cubes: list[tuple[str, int]], verbosity: int = 0) -> list[tuple[str, int]]"},
    {NULL, NULL, 0, NULL} /* Sentinel */
};

/* Module Definition */
static struct PyModuleDef espresso_module = {
    PyModuleDef_HEAD_INIT,
    "_espresso", /* name of module */
    "Espresso logic minimizer binding",
    -1, /* size of per-interpreter state or -1 */
    EspressoMethods};

/* Module Initialization */
PyMODINIT_FUNC PyInit__espresso(void)
{
    return PyModule_Create(&espresso_module);
}

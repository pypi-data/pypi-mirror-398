#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdlib.h>
#include <string.h>

/* Espresso headers */
#include "espresso.h"

static void my_print(set_family_t *F, char *name)
{

    printf("%s\n", name);
    sf_bm_print(F);
    cprint(F);
    printf("-----\n");
}

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
        }
        if (n_cubes > 0)
            family_set = sf_addset(family_set, pcube_container);
    }
    return family_set;
}

static PyObject *espresso_minimize(PyObject *self, PyObject *args)
{
    int nbinary;
    PyObject *mvars, *cubesf_py, *cubesd_py;
    register pcube p, last;
    set_family_t *F;
    set_family_t *D;
    set_family_t *R;
    int verbosity = 0;

    if (!PyArg_ParseTuple(args, "iOOO|i", &nbinary, &mvars, &cubesf_py, &cubesd_py, &verbosity))
    {
        return NULL;
    }
    cube.num_binary_vars = nbinary;
    Py_ssize_t n_mvars = PyList_Size(mvars);
    cube.num_vars = n_mvars + nbinary;
    cube.part_size = ALLOC(int, cube.num_vars);
    for (int i = 0; i < n_mvars; i++)
    {
        int m_size = PyLong_AsLong(PyList_GetItem(mvars, i));
        cube.part_size[nbinary + i] = m_size;
    }

    cube_setup();

    if (verbosity > 0)
    {
        printf("Number of binary variables: %d\n", cube.num_binary_vars);
        printf("Number of multi-valued variables: %d\n", cube.num_mv_vars);
        printf("Sizes (bits) of variables (index, size). Binary has size 2\n");
        for (int i = 0; i < cube.num_vars; i++)
            printf("(%d,%d)", i, cube.part_size[i]);
        printf("\n");
    }
    F = get_family_set(cubesf_py, cube.temp[0]);
    if (verbosity > 0)
        my_print(F, "ON (F)");

    D = get_family_set(cubesd_py, cube.temp[0]);
    if (verbosity > 0)
        my_print(D, "Dont Care (D)");
    R = complement(cube2list(F, D));
    if (verbosity > 0)
        my_print(R, "OFF (R)");

    F = espresso(F, D, R);

    if (verbosity > 0)
        my_print(F, "ON Result");

    PyObject *result = PyList_New(F->count);
    int i = 0;
    foreach_set(F, last, p)
    {
        PyList_SetItem(result, i, PyUnicode_FromString(pc1(p)));
        i++;
    }
    free(F);
    free(D);
    free(R);

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

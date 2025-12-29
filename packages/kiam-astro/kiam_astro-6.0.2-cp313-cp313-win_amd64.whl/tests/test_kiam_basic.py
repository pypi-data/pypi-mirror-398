from kiam_astro import kiam
import unittest
import numpy as np
from numpy.linalg import norm
from numpy import pi

def derivative(func, x0, order, step=1.0e-06):
    """
    Finite-difference derivative of a given function.

    Parameters:
    -----------
    func : Lambda function

    Function to be differentiated.

    x0 : float, numpy.ndarray, shape (n,)

    The point or vector at which the function is differentiated.

    order : int

    Order of differentiation.

    Options: 1, 2, 4

    step : float

    Step of differentiation, the same for all components of x0.

    """
    f0 = func(x0)
    if type(f0) == float or len(f0.shape) == 0:
        f0 = np.reshape(f0, (1,))
    if type(x0) == float or len(x0.shape) == 0:
        x0 = np.reshape(x0, (1,))
    dfdx = np.zeros((f0.size, len(x0)))
    for i in range(len(x0)):
        xp = x0.copy()
        xm = x0.copy()
        if order == 1:
            xp[i] = xp[i] + step
            fp = func(xp)
            dfdx[:, i] = (fp - f0) / step
        elif order == 2:
            xp[i] = xp[i] + step
            xm[i] = xm[i] - step
            fp = func(xp)
            fm = func(xm)
            dfdx[:, i] = (fp - fm) / step / 2.0
        elif order == 4:
            xm2 = x0.copy()
            xp2 = x0.copy()
            xm2[i] = xm2[i] - 2.0*step
            xm[i] = xm[i] - step
            xp[i] = xp[i] + step
            xp2[i] = xp2[i] + 2.0*step
            fm2 = func(xm2)
            fm = func(xm)
            fp = func(xp)
            fp2 = func(xp2)
            dfdx[:, i] = ((1/12)*fm2 - (2/3)*fm + (2/3)*fp - (1/12)*fp2)/step
        else:
            raise 'Unknown order.'
    return dfdx

class TestInputOutput(unittest.TestCase):

    def test_input_output_rv2oe(self):

        rv0 = np.array([1, 0.1, 0.1, 0.1, 1, 0.1])
        oe0 = kiam.rv2oe(rv0, 1.0)
        self.assertIsInstance(oe0, np.ndarray)
        self.assertEqual(oe0.shape, (6,))

        rv0_mat = np.array([[1, 0.1, 0.1, 0.1, 1, 0.1]]).T
        oe0_mat = kiam.rv2oe(rv0_mat, 1.0)
        self.assertIsInstance(oe0_mat, np.ndarray)
        self.assertEqual(oe0_mat.shape, (6, 1))

        np.testing.assert_array_equal(oe0, oe0_mat[:, 0])

        output = kiam.rv2oe(rv0, 1.0, True)
        self.assertIsInstance(output, tuple)
        self.assertEqual(len(output), 2)
        np.testing.assert_array_equal(output[0], oe0)

        output_mat = kiam.rv2oe(rv0_mat, 1.0, True)
        self.assertIsInstance(output_mat, tuple)
        self.assertEqual(len(output_mat), 2)

        np.testing.assert_array_equal(output_mat[0], oe0_mat)
        np.testing.assert_array_equal(output_mat[1][:, :, 0], output[1])

    def test_input_output_oe2rv(self):

        oe0 = np.array([1, 0.1, 0.5, 0.1, 1, 0.1])
        rv0 = kiam.oe2rv(oe0, 1.0)
        self.assertIsInstance(rv0, np.ndarray)
        self.assertEqual(rv0.shape, (6,))

        oe0_mat = np.array([[1, 0.1, 0.5, 0.1, 1, 0.1]]).T
        rv0_mat = kiam.oe2rv(oe0_mat, 1.0)
        self.assertIsInstance(rv0_mat, np.ndarray)
        self.assertEqual(rv0_mat.shape, (6, 1))

        np.testing.assert_array_equal(rv0, rv0_mat[:, 0])

        output = kiam.oe2rv(oe0, 1.0, True)
        self.assertIsInstance(output, tuple)
        self.assertEqual(len(output), 2)

        np.testing.assert_array_equal(output[0], rv0)

        output_mat = kiam.oe2rv(oe0_mat, 1.0, True)
        self.assertIsInstance(output_mat, tuple)
        self.assertEqual(len(output_mat), 2)

        np.testing.assert_array_equal(output_mat[0], rv0_mat)
        np.testing.assert_array_equal(output_mat[1][:, :, 0], output[1])

    def test_input_output_rv2ee(self):

        rv0 = np.array([1, 0.1, 0.1, 0.1, 1, 0.1])
        ee0 = kiam.rv2ee(rv0, 1.0)
        if type(ee0) != np.ndarray or ee0.shape != (6,):
            raise ''

        rv0_mat = np.array([[1, 0.1, 0.1, 0.1, 1, 0.1]]).T
        ee0_mat = kiam.rv2ee(rv0_mat, 1.0)
        if type(ee0_mat) != np.ndarray or ee0_mat.shape != (6, 1):
            raise ''

        np.testing.assert_equal(ee0, ee0_mat[:, 0])

        output = kiam.rv2ee(rv0, 1.0, True)
        if type(output) != tuple or len(output) != 2:
            raise ''

        np.testing.assert_equal(output[0], ee0)

        output_mat = kiam.rv2ee(rv0_mat, 1.0, True)
        if type(output_mat) != tuple or len(output_mat) != 2:
            raise ''

        np.testing.assert_equal(output_mat[0], ee0_mat)
        np.testing.assert_equal(output_mat[1][:, :, 0], output[1])

    def test_input_output_ee2rv(self):

        ee0 = np.array([1, 0.1, 0.2, 0.1, 1, 0.1])
        rv0 = kiam.ee2rv(ee0, 1.0)
        if type(rv0) != np.ndarray or rv0.shape != (6,):
            raise ''

        ee0_mat = np.array([[1, 0.1, 0.2, 0.1, 1, 0.1]]).T
        rv0_mat = kiam.ee2rv(ee0_mat, 1.0)
        if type(rv0_mat) != np.ndarray or rv0_mat.shape != (6, 1):
            raise ''

        np.testing.assert_equal(rv0, rv0_mat[:, 0])

        output = kiam.ee2rv(ee0, 1.0, True)
        if type(output) != tuple or len(output) != 2:
            raise ''

        np.testing.assert_equal(output[0], rv0)

        output_mat = kiam.ee2rv(ee0_mat, 1.0, True)
        if type(output_mat) != tuple or len(output_mat) != 2:
            raise ''

        np.testing.assert_equal(output_mat[0], rv0_mat)
        np.testing.assert_equal(output_mat[1][:, :, 0], output[1])

    def test_input_output_cart2sphere(self):

        cart = np.array([1, 0, 0])
        sphere = kiam.cart2sphere(cart)
        if type(sphere) != np.ndarray or sphere.shape != (3,):
            raise ''

        cart_mat = np.array([[1, 0, 0]]).T
        sphere_mat = kiam.cart2sphere(cart_mat)
        if type(sphere_mat) != np.ndarray or sphere_mat.shape != (3, 1):
            raise ''

        np.testing.assert_equal(sphere, sphere_mat[:, 0])

    def test_input_output_sphere2cart(self):

        sphere = np.array([1, 0.1, 0.1])
        cart = kiam.sphere2cart(sphere)
        if type(cart) != np.ndarray or cart.shape != (3,):
            raise ''

        sphere_mat = np.array([[1, 0.1, 0.1]]).T
        cart_mat = kiam.sphere2cart(sphere_mat)
        if type(cart_mat) != np.ndarray or cart_mat.shape != (3, 1):
            raise ''

        np.testing.assert_equal(cart, cart_mat[:, 0])

    def test_input_output_cart2latlon(self):

        cart = np.array([1, 0, 0])
        latlon = kiam.cart2latlon(cart)
        if type(latlon) != np.ndarray or latlon.shape != (2,):
            raise ''

        cart_mat = np.array([[1, 0, 0]]).T
        latlon_mat = kiam.cart2latlon(cart_mat)
        if type(latlon_mat) != np.ndarray or latlon_mat.shape != (2, 1):
            raise ''

        np.testing.assert_equal(latlon, latlon_mat[:, 0])

    def test_input_output_latlon2cart(self):

        latlon = np.array([1, 2])
        cart = kiam.latlon2cart(latlon)
        if type(cart) != np.ndarray or cart.shape != (3,):
            raise ''

        latlon_mat = np.array([[1, 2]]).T
        cart_mat = kiam.latlon2cart(latlon_mat)
        if type(cart_mat) != np.ndarray or cart_mat.shape != (3, 1):
            raise ''

        np.testing.assert_equal(cart, cart_mat[:, 0])

    def test_input_output_itrs2gcrs(self):

        jd = kiam.juliandate(2022, 11, 22, 0, 0, 0)

        itrs = np.array([1, 0, 0])
        gcrs = kiam.itrs2gcrs(itrs, jd, False)
        if type(gcrs) != np.ndarray or gcrs.shape != (3,):
            raise ''

        itrs_mat = np.array([[1, 0, 0]]).T
        gcrs_mat = kiam.itrs2gcrs(itrs_mat, jd, False)
        if type(gcrs_mat) != np.ndarray or gcrs_mat.shape != (3, 1):
            raise ''

        np.testing.assert_equal(gcrs, gcrs_mat[:, 0])

        output = kiam.itrs2gcrs(itrs, jd, True)
        if type(output) != tuple or len(output) != 2:
            raise ''

        np.testing.assert_equal(output[0], gcrs)

        output_mat = kiam.itrs2gcrs(itrs_mat, jd, True)
        if type(output_mat) != tuple or len(output_mat) != 2:
            raise ''

        np.testing.assert_equal(output_mat[0], gcrs_mat)
        np.testing.assert_equal(output_mat[1][:, :, 0], output[1])

    def test_input_output_gcrs2itrs(self):

        jd = kiam.juliandate(2022, 11, 22, 0, 0, 0)

        gcrs = np.array([1, 0, 0])
        itrs = kiam.gcrs2itrs(gcrs, jd, False)
        if type(itrs) != np.ndarray or itrs.shape != (3,):
            raise ''

        gcrs_mat = np.array([[1, 0, 0]]).T
        itrs_mat = kiam.gcrs2itrs(gcrs_mat, jd, False)
        if type(itrs_mat) != np.ndarray or itrs_mat.shape != (3, 1):
            raise ''

        np.testing.assert_equal(itrs, itrs_mat[:, 0])

        output = kiam.gcrs2itrs(gcrs, jd, True)
        if type(output) != tuple or len(output) != 2:
            raise ''

        np.testing.assert_equal(output[0], itrs)

        output_mat = kiam.gcrs2itrs(gcrs_mat, jd, True)
        if type(output_mat) != tuple or len(output_mat) != 2:
            raise ''

        np.testing.assert_equal(output_mat[0], itrs_mat)
        np.testing.assert_equal(output_mat[1][:, :, 0], output[1])

class TestDirectInverse(unittest.TestCase):

    def test_rv2oe_oe2rv(self):

        rtol = 5.0e-7
        atol = 5.0e-6

        rv0 = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.1])
        oe0, _ = kiam.rv2oe(rv0, 1.0, True)
        np.testing.assert_allclose(oe0, np.array([1.0101010101010102,
                                                  0.009999999999999449,
                                                  0.09966865249116073,
                                                  0.0, 0.0, 0.0]), rtol=1e-13, atol=1e-13)
        rv1, drv1 = kiam.oe2rv(oe0, 1.0, True)
        np.testing.assert_allclose(rv1, rv0, rtol=1e-13, atol=1e-13)

        counter = 0
        for _ in range(1000):
            rv0 = np.random.randn(6)
            mu = 1.0 + np.minimum([np.random.randn() / 5.0], [0.7])
            oe0, doe0 = kiam.rv2oe(rv0, mu, True)
            if oe0[1] < 1e-02 or oe0[1] > 0.9 or oe0[2] < 1e-02:
                continue
            counter = counter + 1
            print('-' * 50)
            print(rv0)
            print(oe0)
            print('-' * 50)
            rv1, drv1 = kiam.oe2rv(oe0, mu, True)
            doe0_true = derivative(lambda x: kiam.rv2oe(x, mu, False), rv0, 4)
            drv1_true = derivative(lambda x: kiam.oe2rv(x, mu, False), oe0, 4)
            np.testing.assert_allclose(rv1, rv0, rtol=rtol, atol=atol)
            np.testing.assert_allclose(np.matmul(doe0, drv1), np.eye(6), rtol=rtol, atol=atol)
            np.testing.assert_allclose(np.matmul(drv1, doe0), np.eye(6), rtol=rtol, atol=atol)
            np.testing.assert_allclose(doe0_true, doe0, rtol=rtol, atol=atol)
            np.testing.assert_allclose(drv1_true, drv1, rtol=rtol, atol=atol)
            oe1, doe1 = kiam.rv2oe(rv1, mu, True)
            np.testing.assert_allclose(oe1, oe0, rtol=rtol, atol=atol)
            np.testing.assert_allclose(doe1, doe0, rtol=rtol, atol=atol)
            rv2, drv2 = kiam.oe2rv(oe1, mu, True)
            np.testing.assert_allclose(rv2, rv1, rtol=rtol, atol=atol)
            np.testing.assert_allclose(drv2, drv1, rtol=rtol, atol=atol)
        print(counter)

    def test_rv2ee_ee2rv(self):

        rtol = 5.0e-8
        atol = 5.0e-8

        rv0 = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
        ee0, _ = kiam.rv2ee(rv0, 1.0, True)
        np.testing.assert_array_equal(ee0, np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]))
        rv1, drv1 = kiam.ee2rv(ee0, 1.0, True)
        np.testing.assert_array_equal(rv1, rv0)

        counter = 0
        for _ in range(1000):
            rv0 = np.random.randn(6)
            mu = 1.0 + np.minimum([np.random.randn()/5.0], [0.7])
            ee0, dee0 = kiam.rv2ee(rv0, mu, True)
            if norm(ee0[1:3]) > 2.0 or norm(ee0[3:5]) > 5.0:
                continue
            counter = counter + 1
            print('-' * 50)
            print(rv0)
            print(ee0)
            print('-' * 50)
            rv1, drv1 = kiam.ee2rv(ee0, mu, True)
            dee0_true = derivative(lambda x: kiam.rv2ee(x, mu, False), rv0, 4)
            drv1_true = derivative(lambda x: kiam.ee2rv(x, mu, False), ee0, 4)
            np.testing.assert_allclose(rv1, rv0, rtol=rtol, atol=atol)
            np.testing.assert_allclose(np.matmul(dee0, drv1), np.eye(6), rtol=rtol, atol=atol)
            np.testing.assert_allclose(np.matmul(drv1, dee0), np.eye(6), rtol=rtol, atol=atol)
            np.testing.assert_allclose(dee0_true, dee0, rtol=rtol, atol=atol)
            np.testing.assert_allclose(drv1_true, drv1, rtol=rtol, atol=atol)
            ee1, dee1 = kiam.rv2ee(rv1, mu, True)
            np.testing.assert_allclose(ee1, ee0, rtol=rtol, atol=atol)
            np.testing.assert_allclose(dee1, dee0, rtol=rtol, atol=atol)
            rv2, drv2 = kiam.ee2rv(ee1, mu, True)
            np.testing.assert_allclose(rv2, rv1, rtol=rtol, atol=atol)
            np.testing.assert_allclose(drv2, drv1, rtol=rtol, atol=atol)
        print(counter)

    def test_cart2sphere_sphere2cart(self):

        x0 = np.array([[0, 0, 1]]).T
        s0 = kiam.cart2sphere(x0)
        np.testing.assert_equal(s0, np.array([[1, 0, 0]]).T)
        x1 = kiam.sphere2cart(s0)
        np.testing.assert_equal(x1, x0)
        s1 = kiam.cart2sphere(x1)
        np.testing.assert_equal(s1, s0)

        x = np.array([[1, 0, 0]]).T
        s = kiam.cart2sphere(x)
        np.testing.assert_equal(s, np.array([[1, 0, np.pi/2]]).T)

    def test_cart2latlon_latlon2cart(self):

        x0 = np.array([[1, 0, 0]]).T
        s0 = kiam.cart2latlon(x0)
        np.testing.assert_equal(s0, np.array([[0, 0]]).T)
        x1 = kiam.latlon2cart(s0)
        np.testing.assert_equal(x1, x0)
        s1 = kiam.cart2latlon(x1)
        np.testing.assert_equal(s1, s0)

    def test_itrs2gcrs_gcrs2itrs(self):

        rtol = 1.0e-13
        atol = 1.0e-13

        for _ in range(100):
            xitrs0 = np.random.randn(3)
            jd = kiam.juliandate(np.random.randint(2020, 2041), np.random.randint(1, 13), np.random.randint(1, 28),
                                          np.random.randint(0, 24), np.random.randint(0, 60), np.random.randint(0, 60))
            xgcrs0, dxgcrs0 = kiam.itrs2gcrs(xitrs0, jd, True)
            xitrs1, dxitrs1 = kiam.gcrs2itrs(xgcrs0, jd, True)
            np.testing.assert_allclose(xitrs1, xitrs0, rtol=rtol, atol=atol)
            np.testing.assert_allclose(dxgcrs0, np.transpose(dxitrs1), rtol=rtol, atol=atol)
            np.testing.assert_allclose(np.matmul(dxgcrs0, dxitrs1), np.eye(3), rtol=rtol, atol=atol)
            xgcrs1, dxgcrs1 = kiam.itrs2gcrs(xitrs1, jd, True)
            np.testing.assert_allclose(xgcrs1, xgcrs0, rtol=rtol, atol=atol)
            np.testing.assert_allclose(dxgcrs1, dxgcrs0, rtol=rtol, atol=atol)
            xitrs2, dxitrs2 = kiam.gcrs2itrs(xgcrs1, jd, True)
            np.testing.assert_allclose(xitrs2, xitrs1, rtol=rtol, atol=atol)
            np.testing.assert_allclose(dxitrs2, dxitrs1, rtol=rtol, atol=atol)

    def test_scrs2mer_mer2scrs(self):

        rtol = 1.0e-13
        atol = 1.0e-13

        for _ in range(100):
            xscrs0 = np.random.randn(3, 1)
            jd = kiam.juliandate(np.random.randint(2020, 2041), np.random.randint(1, 13),
                                          np.random.randint(1, 28),
                                          np.random.randint(0, 24), np.random.randint(0, 60), np.random.randint(0, 60))
            xmer0, dxmer0 = kiam.scrs2mer(xscrs0, jd, True)
            xscrs1, dxscrs1 = kiam.mer2scrs(xmer0, jd, True)
            np.testing.assert_allclose(xscrs1, xscrs0, rtol=rtol, atol=atol)
            np.testing.assert_allclose(dxmer0[:, :, 0], np.transpose(dxscrs1[:, :, 0]), rtol=rtol, atol=atol)
            np.testing.assert_allclose(np.matmul(dxmer0[:, :, 0], dxscrs1[:, :, 0]), np.eye(3), rtol=rtol, atol=atol)
            xmer1, dxmer1 = kiam.scrs2mer(xscrs1, jd, True)
            np.testing.assert_allclose(xmer1, xmer0, rtol=rtol, atol=atol)
            np.testing.assert_allclose(dxmer1, dxmer0, rtol=rtol, atol=atol)

    def test_scrs2gcrs_gcrs2scrs(self):

        rtol = 1.0e-10
        atol = 1.0e-10

        for _ in range(100):
            xscrs0 = np.random.randn(6, 1)
            jd = kiam.juliandate(np.random.randint(2020, 2041), np.random.randint(1, 13),
                                          np.random.randint(1, 28),
                                          np.random.randint(0, 24), np.random.randint(0, 60), np.random.randint(0, 60))
            xgcrs0 = kiam.scrs2gcrs(xscrs0, jd, 1.0, 1.0)
            xscrs1 = kiam.gcrs2scrs(xgcrs0, jd, 1.0, 1.0)
            np.testing.assert_allclose(xscrs1, xscrs0, rtol=rtol, atol=atol)
            xgcrs1 = kiam.scrs2gcrs(xscrs1, jd, 1.0, 1.0)
            np.testing.assert_allclose(xgcrs1, xgcrs0, rtol=rtol, atol=atol)

    def test_crs2ers_ers2crs(self):

        rtol = 1.0e-10
        atol = 1.0e-10

        for _ in range(1000):
            xcrs0 = np.random.randn(6, 1)
            xers0 = kiam.crs2ers(xcrs0)
            xcrs1 = kiam.ers2crs(xers0)
            np.testing.assert_allclose(xcrs1, xcrs0, rtol=rtol, atol=atol)
            xers1 = kiam.crs2ers(xcrs1)
            np.testing.assert_allclose(xers1, xers0, rtol=rtol, atol=atol)

    def test_hscrs2gcrs_gcrs2hcrs(self):

        rtol = 1.0e-8
        atol = 1.0e-8

        for _ in range(100):
            xhcrs0 = np.random.randn(6, 1)*1000.0
            jd = kiam.juliandate(np.random.randint(2020, 2041), np.random.randint(1, 13),
                                          np.random.randint(1, 28),
                                          np.random.randint(0, 24), np.random.randint(0, 60), np.random.randint(0, 60))
            xgcrs0 = kiam.hcrs2gcrs(xhcrs0, jd, 1.0, 1.0)
            xhcrs1 = kiam.gcrs2hcrs(xgcrs0, jd, 1.0, 1.0)
            np.testing.assert_allclose(xhcrs1, xhcrs0, rtol=rtol, atol=atol)
            xgcrs1 = kiam.hcrs2gcrs(xhcrs1, jd, 1.0, 1.0)
            np.testing.assert_allclose(xgcrs1, xgcrs0, rtol=rtol, atol=atol)

    def test_scrs2sors_sors2scrs(self):

        rtol = 1.0e-11
        atol = 1.0e-11

        for _ in range(100):
            xscrs0 = np.random.randn(6, 1)
            xscrs0[0:3] = xscrs0[0:3] * 10000.0
            jd = kiam.juliandate(np.random.randint(2020, 2041), np.random.randint(1, 13),
                                          np.random.randint(1, 28),
                                          np.random.randint(0, 24), np.random.randint(0, 60), np.random.randint(0, 60))
            xsors0, dxsors0 = kiam.scrs2sors(xscrs0, jd, True)
            xscrs1, dxscrs1 = kiam.sors2scrs(xsors0, jd, True)
            np.testing.assert_allclose(xscrs1, xscrs0, rtol=rtol, atol=atol)
            np.testing.assert_allclose(dxsors0[:, :, 0], np.transpose(dxscrs1[:, :, 0]), rtol=rtol, atol=atol)
            np.testing.assert_allclose(np.matmul(dxsors0[:, :, 0], dxscrs1[:, :, 0]), np.eye(6), rtol=rtol, atol=atol)
            xsors1, dxsors1 = kiam.scrs2sors(xscrs1, jd, True)
            np.testing.assert_allclose(xsors1, xsors0, rtol=rtol, atol=atol)
            np.testing.assert_allclose(dxsors1, dxsors0, rtol=rtol, atol=atol)

    def test_ine2rotEph_rot2ineEph(self):

        rtol = 1.0e-13
        atol = 1.0e-13

        for _ in range(100):
            xine0 = np.random.randn(6, 1)
            jd = kiam.juliandate(np.random.randint(2020, 2041), np.random.randint(1, 13),
                                          np.random.randint(1, 28),
                                          np.random.randint(0, 24), np.random.randint(0, 60), np.random.randint(0, 60))
            xrot0 = kiam.ine2rot_eph(xine0, jd, 'Earth', 'Moon', 1.0, 1.0)
            xine1 = kiam.rot2ine_eph(xrot0, jd, 'Earth', 'Moon', 1.0, 1.0)
            np.testing.assert_allclose(xine1, xine0, rtol=rtol, atol=atol)
            xrot1 = kiam.ine2rot_eph(xine1, jd, 'Earth', 'Moon', 1.0, 1.0)
            np.testing.assert_allclose(xrot1, xrot0, rtol=rtol, atol=atol)

    def test_ine2rot_rot2ine(self):

        rtol = 1.0e-13
        atol = 1.0e-13

        for _ in range(100):
            xine0 = np.random.randn(6, 1)
            t = 1.0
            t0 = 0.0
            xrot0 = kiam.ine2rot(xine0, t, t0)
            xine1 = kiam.rot2ine(xrot0, t, t0)
            np.testing.assert_allclose(xine1, xine0, rtol=rtol, atol=atol)
            xrot1 = kiam.ine2rot(xine1, t, t0)
            np.testing.assert_allclose(xrot1, xrot0, rtol=rtol, atol=atol)

    def test_mer2lvlh_lvlh2mer(self):

        rtol = 1.0e-13
        atol = 1.0e-13

        for _ in range(100):
            xmer0 = np.random.randn(3,)
            lat = np.random.rand() * pi - pi / 2
            lon = np.random.rand() * 2 * pi
            xlvlh0 = kiam.mer2lvlh(xmer0, lat, lon)
            xmer1 = kiam.lvlh2mer(xlvlh0, lat, lon)
            xlvlh1 = kiam.mer2lvlh(xmer1, lat, lon)
            np.testing.assert_allclose(xmer0, xmer1, rtol=rtol, atol=atol)
            np.testing.assert_allclose(xlvlh0, xlvlh1, rtol=rtol, atol=atol)

class PlottingRoutines(unittest.TestCase):

    def test_plot(self):
        x = np.array([1, 2, 3, 4, 5])
        y1 = np.array([2, 3, 0, 1, 2])
        y2 = np.array([3, 4, 1, 2, 3])
        fig = kiam.plot(x, y1, xlabel=r'$x\text{, Earth radii}$', name='blue')
        self.assertIsNotNone(fig, "Figure should be created")
        fig = kiam.plot(x, y2, fig, xlabel=r'$x\text{, Earth radii}$', name='red')
        self.assertIsNotNone(fig, "Figure should be created")

    def test_plot3(self):
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 3, 0, 1, 2])
        z1 = np.array([3, 4, 1, 2, 3])
        z2 = np.array([4, 5, 2, 3, 4])
        fig = kiam.plot3(x, y, z1, name='blue')
        self.assertIsNotNone(fig, "Figure should be created")
        fig = kiam.plot3(x, y, z2, fig, name='red')
        self.assertIsNotNone(fig, "Figure should be created")

    def test_polar_plot(self):
        r = np.array([0.5, 1, 2, 2.5, 3, 4])
        theta = np.array([35, 70, 120, 155, 205, 240])
        fig = kiam.polar_plot(r, theta, 'lines+markers')
        self.assertIsNotNone(fig, "Figure should be created")

    def test_box_plot(self):
        y0 = np.random.randn(50) - 1
        y1 = np.random.randn(50) + 1
        fig = kiam.box_plot(y0, y1)
        self.assertIsNotNone(fig, "Figure should be created")

class TestConstants(unittest.TestCase):

    def test_units_celestial_bodies(self):
        """Test units function for various celestial bodies and systems."""

        # Test 1: Single body - Sun
        sun_units = kiam.units('sun')
        self.assertIsInstance(sun_units, dict, "Should return a dictionary")
        self.assertAlmostEqual(sun_units['GM'], 132712440040.0, msg="Sun GM should match standard value")
        self.assertAlmostEqual(sun_units['DistUnit'], 149597870.7, msg="Sun distance unit (AU) should be correct")

        # Test 2: Single body - Mercury
        mercury_units = kiam.units('mercury')
        self.assertAlmostEqual(mercury_units['GM'], 22032.08049007238, msg="Mercury GM should match")
        self.assertAlmostEqual(mercury_units['SunGM'], 6023600.0, msg="Sun GM in Mercury units should be correct")

        # Test 3: Single body - Earth
        earth_units = kiam.units('earth')
        self.assertAlmostEqual(earth_units['GM'], 398600.4356, msg="Earth GM should match standard value")
        self.assertAlmostEqual(earth_units['DistUnit'], 6371.0084, msg="Earth radius should be correct")
        self.assertAlmostEqual(earth_units['MoonGM'], 0.0123000371, msg="Moon GM in Earth units should be correct")

        # Test 4: Single body - Moon
        moon_units = kiam.units('moon')
        self.assertAlmostEqual(moon_units['GM'], 4902.800145956161, msg="Moon GM should match")
        self.assertAlmostEqual(moon_units['EarthGM'], 81.30056778, msg="Earth GM in Moon units should be ~81")

        # Test 5: Single body - Jupiter
        jupiter_units = kiam.units('jupiter')
        self.assertAlmostEqual(jupiter_units['GM'], 126712762.55550297, msg="Jupiter GM should match")
        self.assertAlmostEqual(jupiter_units['SaturnGM'], 0.29942196, msg="Saturn GM in Jupiter units should be ~0.3")

        # Test 6: Two-body system - Sun-Mercury
        sun_mercury = kiam.units('sun', 'mercury')
        self.assertIn('mu', sun_mercury, "Two-body system should have 'mu' key")
        self.assertAlmostEqual(sun_mercury['mu'], 1.6601365e-07, msg="Mercury mu (relative to Sun) should be correct")
        self.assertAlmostEqual(sun_mercury['DistUnit'], 57909226.54152438, msg="Sun-Mercury distance unit should be ~0.387 AU")

        # Test 7: Two-body system - Sun-Earth
        sun_earth = kiam.units('sun', 'earth')
        self.assertAlmostEqual(sun_earth['mu'], 3.0404234e-06, msg="Earth-Moon system mu should be correct")
        self.assertAlmostEqual(sun_earth['DistUnit'], 149598261.1504425, msg="Sun-Earth distance should be ~1 AU")
        self.assertAlmostEqual(sun_earth['SunGM'], 0.9999969595, msg="Sun GM should be close to 1.0 in normalized units")

        # Test 8: Two-body system - Earth-Moon
        earth_moon = kiam.units('earth', 'moon')
        self.assertAlmostEqual(earth_moon['mu'], 0.01215058446, msg="Moon mu in Earth-Moon system should be ~0.0121")
        self.assertAlmostEqual(earth_moon['DistUnit'], 384402.0, msg="Earth-Moon distance should be correct")
        self.assertAlmostEqual(earth_moon['EarthGM'], 0.98784941, msg="Earth GM in Earth-Moon barycentric system")

        # Test 9: Two-body system - Sun-Jupiter
        sun_jupiter = kiam.units('sun', 'jupiter')
        self.assertAlmostEqual(sun_jupiter['mu'], 0.00095388114, msg="Jupiter mu should be ~0.001")
        self.assertAlmostEqual(sun_jupiter['SunGM'], 0.99904611, msg="Sun GM should be slightly less than 1.0 (barycentric)")

        # Test 10: Two-body system - Sun-Neptune
        sun_neptune = kiam.units('sun', 'neptune')
        self.assertAlmostEqual(sun_neptune['mu'], 5.151e-05, msg="Neptune mu should be correct")
        self.assertAlmostEqual(sun_neptune['NeptuneGM'], 5.151e-05, msg="Neptune GM should equal mu in this system")

if __name__ == '__main__':
    unittest.main()
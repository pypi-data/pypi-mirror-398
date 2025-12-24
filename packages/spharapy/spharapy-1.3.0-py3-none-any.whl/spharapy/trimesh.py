"""Triangular mesh data

This module provides a class for storing triangular meshes. Attributes
of the triangular mesh can be determined. In addition, methodes are available
to derive further information from the triangular grid.

"""

import copy

import numpy as np

def area_triangle(vertex1, vertex2, vertex3):
    """Estimate the area of a triangle given by three vertices

    The area of the triangle given by three vertices is calculated by the half
    cross product formula.

    Parameters
    ----------
    vertex1 : array, shape (1, 3)
    vertex2 : array, shape (1, 3)
    vertex3 : array, shape (1, 3)


    Returns
    -------
    trianglearea : float
        Area of the triangle given by the three vertices.


    Examples
    --------

    >>> from spharapy import trimesh as tm
    >>> tm.area_triangle([1, 0, 0], [0, 1, 0], [0, 0, 1])
    0.8660254037844386

    """
    vertex1 = np.asarray(vertex1)
    vertex2 = np.asarray(vertex2)
    vertex3 = np.asarray(vertex3)

    trianglearea = 0.5 * np.linalg.norm(np.cross(vertex2 - vertex1, vertex3 - vertex1))
    return trianglearea


def side_lens_triangle(vertex1, vertex2, vertex3):
    """Estimate the three side length of a triangle given by three vertices

    Parameters
    ----------
    vertex1 : array, shape (1, 3)
    vertex2 : array, shape (1, 3)
    vertex3 : array, shape (1, 3)


    Returns
    -------
    side_lens : array, shape (1, 3)
        Side lengths of the triangle given by the three vertices.


    Examples
    --------

    >>> from spharapy import trimesh as tm
    >>> tm.side_lens_triangle([1, 0, 0], [0, 1, 0], [0, 0, 1])
    array([1.41421356, 1.41421356, 1.41421356])

    """
    vertex1 = np.asarray(vertex1)
    vertex2 = np.asarray(vertex2)
    vertex3 = np.asarray(vertex3)

    side_lens = np.array(
        [
            np.linalg.norm(vertex2 - vertex1),
            np.linalg.norm(vertex3 - vertex2),
            np.linalg.norm(vertex1 - vertex3),
        ]
    )

    return side_lens


def angles_triangle(vertex1, vertex2, vertex3):
    """Estimate the three internal angles of a triangle given by three vertices

    Parameters
    ----------
    vertex1 : array, shape (1, 3)
    vertex2 : array, shape (1, 3)
    vertex3 : array, shape (1, 3)


    Returns
    -------
    angles : array, shape (1, 3)
        Internal angles of the triangle given by the three vertices.


    Examples
    --------

    >>> from spharapy import trimesh as tm
    >>> tm.angles_triangle([1, 0, 0], [0, 1, 0], [0, 0, 1])
    array([1.04719755, 1.04719755, 1.04719755])


    """
    vertex1 = np.asarray(vertex1)
    vertex2 = np.asarray(vertex2)
    vertex3 = np.asarray(vertex3)

    # compute unit vectors in direction of the triangle sides
    v1 = vertex2 - vertex1
    v1 = v1 / np.linalg.norm(v1)
    v2 = vertex3 - vertex2
    v2 = v2 / np.linalg.norm(v2)
    v3 = vertex1 - vertex3
    v3 = v3 / np.linalg.norm(v3)

    # compute the internal angles of the triangle
    angles = np.array(
        [
            np.arccos(np.clip(np.dot(v1, -v3), -1.0, 1.0)),
            np.arccos(np.clip(np.dot(v2, -v1), -1.0, 1.0)),
            np.arccos(np.clip(np.dot(v3, -v2), -1.0, 1.0)),
        ]
    )

    return angles


class TriMesh:
    """Triangular mesh class

    This class can be used to store data to define a triangular mesh and it
    provides atributes and methodes to derive further information about the
    triangular mesh.

    Parameters
    ----------
    trilist: array, shape (n_triangles, 3)
        List of triangles, each row of the array contains the edges of
        a triangle. The edges of the triangles are defined by the
        indices to the list of vertices. The index of the first vertex
        is 0. The number of triangles is n_triangles.
    vertlist: array, shape (n_points, 3)
        List of coordinates x, y, z which describes the positions of the
        vertices.

    Attributes
    ----------
    trilist: array, shape (n_triangles, 3)
        List of triangles of the mesh.
    vertlist: array, shape (n_points, 3)
        List of coordinates of the vertices
    """

    def __init__(self, trilist, vertlist):
        self.trilist = np.asarray(trilist)
        self.vertlist = np.asarray(vertlist)

    @property
    def trilist(self):
        """Get or set the list of triangles.

        Setting the list of triangles will simultaneously check if the
        triangle list is in the correct format.
        """

        return self._trilist

    @trilist.setter
    def trilist(self, trilist):
        if trilist.ndim != 2:
            raise ValueError("Triangle list has to be 2D!")
        elif trilist.shape[1] != 3:
            raise ValueError("Each entry of the triangle list has to consist of three elements!")
        # pylint: disable=W0201
        self._trilist = np.asarray(trilist)

    @property
    def vertlist(self):
        """Get or set the list of vertices.

        Setting the list of triangles will simultaneously check if the
        vertice list is in the correct format.
        """

        return self._vertlist

    @vertlist.setter
    def vertlist(self, vertlist):
        if vertlist.ndim != 2:
            raise ValueError("Vertex list has to be 2D!")
        elif vertlist.shape[1] != 3:
            raise ValueError("Each entry of the vertex list has to consist of three elements!")
        # pylint: disable=W0201
        self._vertlist = np.asarray(vertlist)

    def weightmatrix(self, mode="inv_euclidean"):
        """Compute a weight matrix for a triangular mesh

        The method creates a weighting matrix for the edges of a triangular
        mesh using different weighting function.

        Parameters
        ----------
        mode : {'unit', 'inv_euclidean', 'half_cotangent'}, optional
            The parameter `mode` specifies the method for determining
            the edge weights. Using the option 'unit' all edges of the
            mesh are weighted by unit weighting function, the result
            is an adjacency matrix. The option 'inv_euclidean' results
            in edge weights corresponding to the inverse Euclidean
            distance of the edge lengths. The option 'half_cotangent'
            uses the half of the cotangent of the two angles opposed
            to an edge as weighting function. the default weighting
            function is 'inv_euclidean'.

        Returns
        -------
        weightmatrix : array, shape (n_points, n_points)
            Symmetric matrix, which contains the weight of the edges
            between adjacent vertices. The number of vertices of the
            triangular mesh is n_points.

        Examples
        --------

        >>> from spharapy import trimesh as tm
        >>> testtrimesh = tm.TriMesh([[0, 1, 2]], [[1., 0., 0.], [0., 2., 0.],
        ...                                        [0., 0., 3.]])
        >>> testtrimesh.weightmatrix(mode='inv_euclidean')
        array([[ 0.        ,  0.4472136 ,  0.31622777],
               [ 0.4472136 ,  0.        ,  0.2773501 ],
               [ 0.31622777,  0.2773501 ,  0.        ]])

        """

        # plausibility test of option 'mode'
        if mode not in ("unit", "inv_euclidean", "half_cotangent"):
            raise ValueError("Unrecognized mode '{mode}'")

        # get the largest index from from triangle list
        maxindex = self.trilist.max()

        # fill the weight matrix with zeros, the size is (maxindex + 1)^2
        weightmatrix = np.zeros((maxindex + 1, maxindex + 1), dtype=float)

        if mode == "unit":
            # iterate over triangle list an build weight matrix
            for x in self.trilist:
                weightmatrix[x[0], x[1]] = 1
                weightmatrix[x[1], x[0]] = 1

                weightmatrix[x[0], x[2]] = 1
                weightmatrix[x[2], x[0]] = 1

                weightmatrix[x[1], x[2]] = 1
                weightmatrix[x[2], x[1]] = 1

        elif mode == "inv_euclidean":
            # iterate over triangle list an build weight matrix
            for x in self.trilist:
                # compute the three vectors of the triangle
                vec10 = self.vertlist[x[1]] - self.vertlist[x[0]]
                vec20 = self.vertlist[x[2]] - self.vertlist[x[0]]
                vec21 = self.vertlist[x[2]] - self.vertlist[x[1]]

                # fill in the weights in the weight matrix
                weightmatrix[x[0], x[1]] = 1 / np.linalg.norm(vec10)
                weightmatrix[x[1], x[0]] = 1 / np.linalg.norm(vec10)
                weightmatrix[x[0], x[2]] = 1 / np.linalg.norm(vec20)
                weightmatrix[x[2], x[0]] = 1 / np.linalg.norm(vec20)
                weightmatrix[x[2], x[1]] = 1 / np.linalg.norm(vec21)
                weightmatrix[x[1], x[2]] = 1 / np.linalg.norm(vec21)

        else:
            # iterate over triangle list an build weight matrix
            for x in self.trilist:
                # compute the directional vectors at the 1st vertex
                vec1 = self.vertlist[x[1]] - self.vertlist[x[0]]
                vec2 = self.vertlist[x[2]] - self.vertlist[x[0]]

                # compute the weight of the edge 0.5 * cot
                tempweight = 0.5 * (
                    1.0
                    / np.tan(
                        np.arccos(
                            np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
                        )
                    )
                )

                weightmatrix[x[1], x[2]] += tempweight
                weightmatrix[x[2], x[1]] += tempweight

                # compute the directional vectors at the 2nd vertex
                vec1 = self.vertlist[x[0]] - self.vertlist[x[1]]
                vec2 = self.vertlist[x[2]] - self.vertlist[x[1]]

                # compute the weight of the edge 0.5 * cot
                tempweight = 0.5 * (
                    1.0
                    / np.tan(
                        np.arccos(
                            np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
                        )
                    )
                )

                weightmatrix[x[0], x[2]] += tempweight
                weightmatrix[x[2], x[0]] += tempweight

                # compute the directional vectors at the 3rd vertex
                vec1 = self.vertlist[x[0]] - self.vertlist[x[2]]
                vec2 = self.vertlist[x[1]] - self.vertlist[x[2]]

                # compute the weight of the edge 0.5 * cot
                tempweight = 0.5 * (
                    1.0
                    / np.tan(
                        np.arccos(
                            np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
                        )
                    )
                )

                weightmatrix[x[0], x[1]] += tempweight
                weightmatrix[x[1], x[0]] += tempweight

        # return the weight matrix
        return weightmatrix

    def laplacianmatrix(self, mode="inv_euclidean"):
        """Compute a laplacian matrix for a triangular mesh

        The method creates a laplacian matrix for a triangular
        mesh using different weighting function.

        Parameters
        ----------
        mode : {'unit', 'inv_euclidean', 'half_cotangent'}, optional
            The methods for determining the edge weights. Using the option
            'unit' all edges of the mesh are weighted by unit weighting
            function, the result is an adjacency matrix. The option
            'inv_euclidean' results in edge weights corresponding to the
            inverse Euclidean distance of the edge lengths. The option
            'half_cotangent' uses the half of the cotangent of the two angles
            opposed to an edge as weighting function. the default weighting
            function is 'inv_euclidean'.

        Returns
        -------
        laplacianmatrix : array, shape (n_points, n_points)
            Matrix, which contains the discrete laplace operator for data
            defined at the vertices of a triangular mesh. The number of
            vertices of the triangular mesh is n_points.

        Examples
        --------

        >>> from spharapy import trimesh as tm
        >>> testtrimesh = tm.TriMesh([[0, 1, 2]], [[1., 0., 0.], [0., 2., 0.],
        ...                                        [0., 0., 3.]])
        >>> testtrimesh.laplacianmatrix(mode='inv_euclidean')
        array([[ 0.76344136, -0.4472136 , -0.31622777],
               [-0.4472136 ,  0.72456369, -0.2773501 ],
               [-0.31622777, -0.2773501 ,  0.59357786]])

        """

        # plausibility test of option 'mode'
        if mode not in ("unit", "inv_euclidean", "half_cotangent"):
            raise ValueError("Unrecognized mode '{mode}'")

        # determine the weight matrix with
        weightmatrix = self.weightmatrix(mode=mode)

        # compute the laplacian matrix
        laplacianmatrix = np.diag(weightmatrix.sum(axis=0)) - weightmatrix

        # return the laplacian matrix
        return laplacianmatrix

    def massmatrix(self, mode="normal"):
        """Mass matrix of a triangular mesh

        The method determines a mass matrix of a triangular mesh.

        Parameters
        ----------

        mode : {'normal', 'lumped'}, optional
            The `mode` parameter can be used to select whether a normal mass
            matrix or a lumped mass matrix is to be determined.

        Returns
        -------
        massmatrix : array, shape (n_points, n_points)
            Symmetric matrix, which contains the mass values for each edge and
            vertex for the FEM approch. The number of vertices of the
            triangular mesh is n_points.

        Examples
        --------

        >>> from spharapy import trimesh as tm
        >>> testtrimesh = tm.TriMesh([[0, 1, 2]], [[1., 0., 0.], [0., 2., 0.],
        ...                                        [0., 0., 3.]])
        >>> testtrimesh.massmatrix()
        array([[ 0.58333333,  0.29166667,  0.29166667],
               [ 0.29166667,  0.58333333,  0.29166667],
               [ 0.29166667,  0.29166667,  0.58333333]])

        References
        ----------
        :cite:`vallet07,dyer07,zhang07`

        """

        # plausibility test of option 'mode'
        if mode not in ("normal", "lumped"):
            raise ValueError("Unrecognized mode '{mode}'")

        # get the largest index from from triangle list
        maxindex = self.trilist.max()

        # fill the weight matrix with zeros, the size is (maxindex + 1)^2
        massmatrix = np.zeros((maxindex + 1, maxindex + 1), dtype=float)

        if mode == "lumped":
            # iterate over triangle list an build mass matrix
            for x in self.trilist:
                # compute the area of the triangle
                temparea = area_triangle(
                    self.vertlist[x[0]], self.vertlist[x[1]], self.vertlist[x[2]]
                )

                # add to every matrix element belonging to the vertex v(i) of
                # the triangle a 3rd of the triangle area
                massmatrix[x[0], x[0]] += temparea / 3
                massmatrix[x[1], x[1]] += temparea / 3
                massmatrix[x[2], x[2]] += temparea / 3
        else:
            # iterate over triangle list an build mass matrix
            for x in self.trilist:
                # compute the area of the triangle
                temparea = area_triangle(
                    self.vertlist[x[0]], self.vertlist[x[1]], self.vertlist[x[2]]
                )

                # add to every matrix element belonging to the edge e(i,j) of
                # the triangle a twelfth of the triangle area
                massmatrix[x[0], x[1]] += temparea / 12
                massmatrix[x[1], x[0]] = massmatrix[x[0], x[1]]
                massmatrix[x[0], x[2]] += temparea / 12
                massmatrix[x[2], x[0]] = massmatrix[x[0], x[2]]
                massmatrix[x[1], x[2]] += temparea / 12
                massmatrix[x[2], x[1]] = massmatrix[x[1], x[2]]

                # add to every matrix element belonging to the vertex v(i) of
                # the triangle a sixth of the triangle area
                massmatrix[x[0], x[0]] += temparea / 6
                massmatrix[x[1], x[1]] += temparea / 6
                massmatrix[x[2], x[2]] += temparea / 6

        # return the mass matrix
        return massmatrix

    def stiffnessmatrix(self):
        """Stiffness matrix of a triangular mesh

        The method determines a stiffness matrix of a triangular mesh.

        Returns
        -------
        stiffmatrix : array, shape (n_points, n_points)
            Symmetric matrix, which contains the stiffness values for each edge
            and vertex for the FEM approch. The number of vertices of the
            triangular mesh is n_points.

        Examples
        --------

        >>> from spharapy import trimesh as tm
        >>> testtrimesh = tm.TriMesh([[0, 1, 2]], [[1., 0., 0.], [0., 2., 0.],
        ...                                        [0., 0., 3.]])
        >>> testtrimesh.stiffnessmatrix()
        array([[-0.92857143,  0.64285714,  0.28571429],
               [ 0.64285714, -0.71428571,  0.07142857],
               [ 0.28571429,  0.07142857, -0.35714286]])

        References
        ----------
        :cite:`vallet07`

        """

        # get the largest index from from triangle list
        maxindex = self.trilist.max()

        # fill the weight matrix with zeros, the size is (maxindex + 1)^2
        stiffmatrix = np.zeros((maxindex + 1, maxindex + 1), dtype=float)

        # compute the cot weight matrix
        weightmatrix = self.weightmatrix(mode="half_cotangent")

        # compute and return the stiffness matrix
        stiffmatrix = -np.diag(weightmatrix.sum(axis=0)) + weightmatrix

        return stiffmatrix

    def one_ring_neighborhood(self, vertex_index=0):
        """The 1 ring neighborhood of a vertex

        The method determines all adjacent vertices of a vertex that
        is given by its index, the so called 1 ring neighborhood.

        Parameters
        ----------
        vertex_index : integer
            Index of the vertex for which the adjacent vertices are to
            be determined. The index must be in the range 0 to number of
            vertices - 1.

        Returns
        -------
        one_ring_neighborhood : array, shape (1, n)
            Array of indexes on vertices adjacent to a given vertex.
        """
        # plausibility test of vertex_index
        # is the index of type integer
        if not isinstance(vertex_index, (int | np.integer)):
            raise TypeError("""The parameter vertex_index has to be
            int.""")
        # is the index within the interval (0, maxindex_vertlist)
        if (vertex_index < 0) or (vertex_index > self.vertlist.shape[0]):
            raise IndexError("""The vertex_index is out of range.""")

        # get the adjacent triangles to a vertex
        adjacent_tri = self.trilist[(self.trilist == vertex_index).any(axis=1)]

        # geth the indices of vertices of the triangles
        one_ring_neighborhood = np.unique(adjacent_tri)

        # remove the center vertex
        one_ring_neighborhood = one_ring_neighborhood[one_ring_neighborhood != vertex_index]

        return one_ring_neighborhood

    def adjacent_tri(self, vertex_index=0):
        """All triangles with the given vertex

        The method determined all triangles of the triangular mesh that
        contain the given vertex.

        Parameters
        ----------
        vertex_index : integer
            Index of the vertex for which the adjacent vertices are to
            be determined. The index must be in the range 0 to number of
            vertices - 1.

        Returns
        -------
        tri_with_vertex : array, shape (3, n)
            List of triangles containing the given vertex.
        """
        # plausibility test of vertex_index
        # is the index of type integer
        if not isinstance(vertex_index, (int | np.integer)):
            raise TypeError("""The parameter vertex_index has to be
            int.""")
        # is the index within the interval (0, maxindex_vertlist)
        if (vertex_index < 0) or (vertex_index > self.vertlist.shape[0]):
            raise IndexError("""The vertex_index is out of range.""")

        # get the adjacent triangles to a vertex
        adjacent_tri = self.trilist[(self.trilist == vertex_index).any(axis=1)]

        return adjacent_tri

    def is_edge(self, vertex1_index, vertex2_index):
        """Are 2 vertices connected by an edge

        The method determines whether two vertices are connected by an
        edge in the triangle mesh and if so, whether it is an internal
        edge or a boundary edge.

        Parameters
        ----------
        vertex1_index, vertex2_index : integer
            Indeces of the two vertices. The index must be in the range
            0 to number of vertices - 1.

        Returns
        -------
        is_edge : integer
            0 if vertex1 and vertex2 are not connected by a single edge,
            1 if vertex1 and vertex2 are connected by a boundary edge,
            2 if vertex1 and vertex2 are connected by an internal edge.
        """
        # plausibility test of vertex_index
        # is the index of type integer
        if (not isinstance(vertex1_index, (int | np.integer))) or (
            not isinstance(vertex2_index, (int | np.integer))
        ):
            raise TypeError("""The parameters vertex1|2_index has to be
            int.""")

        # is the index within the interval (0, maxindex_vertlist)
        if (
            (vertex1_index < 0)
            or (vertex1_index > self.vertlist.shape[0])
            or (vertex2_index < 0)
            or (vertex2_index > self.vertlist.shape[0])
        ):
            raise IndexError("""The vertex1|2_index is out of range.""")

        # Determine the number of triangles in which the searched edge is
        # contained and return it.
        tri_with_edge = self.trilist[
            np.logical_and(
                (self.trilist == vertex1_index).any(axis=1),
                (self.trilist == vertex2_index).any(axis=1),
            )
        ]
        return len(tri_with_edge)

    def remove_vertices(self, vertex_index_list):
        """Remove vertices from a triangular mesh

        The method removes vertices from a triangle mesh.
        The Half-edge Collapse method is used. The positions of the
        remaining vertices are not affected and they are
        retriangulated.

        Parameters
        ----------
        vertex_index_list : vector of ints
            Indices of the vertices to remove from the mesh. The indices
            must be in the range 0 to number of vertices - 1.

        Returns
        -------
        triangsamples : trimesh object
            A trimesh object from the package spharapy, where the given
            vertices are removed.

        """
        # create a numpy array with unique indices to vertices to delete
        vertex_index_list = np.unique(vertex_index_list)
        # sort the index list in descending order
        vertex_index_list[::-1].sort()

        # plausibility test of vertex_index_list
        # is the index of type integer
        if vertex_index_list.ndim != 1:
            raise TypeError("""The parameter vertex_index_list has to be
            a 1D vector of int.""")

        if not all(isinstance(i, (int | np.integer)) for i in vertex_index_list):
            raise TypeError("""The parameter vertex_index_list has to be
            a 1D vector of int.""")

        # is the index within the interval (0, maxindex_vertlist)
        if (vertex_index_list.min() < 0) or (vertex_index_list.max() > self.vertlist.shape[0]):
            raise IndexError("""The vertex_index is out of range.""")

        # create a deep copy
        temp_trimesh = copy.deepcopy(self)

        # iterate over the list of indices to be deleted
        for vertex_index in vertex_index_list:
            # determine all neighbor vertices of vertex in iteration
            neighbor_vert = temp_trimesh.one_ring_neighborhood(vertex_index)

            # determine all adjacent triangles of the given vertex
            adjacent_tri = temp_trimesh.adjacent_tri(vertex_index)

            # determine the type of edges to the neighbor vertices
            type_of_edges = np.asarray(
                [temp_trimesh.is_edge(vertex_index, vert_i) for vert_i in neighbor_vert]
            )

            # measure the 'distortion' of the mesh if a give edge is
            # 'half-colpsee', the measure is the deviation of the newly
            # generated triangles from equilateralism

            # 1st allocate mem
            dist_measure = np.zeros(len(neighbor_vert))

            # Iterate over all neighbour vertices of the vertex to be deleted
            for j, vert_i in enumerate(neighbor_vert):
                # Remove triangles containing the neighbour vertex
                temp_tri = adjacent_tri[(adjacent_tri != vert_i).all(axis=1), :]

                # Map the vertex to be deleted to the neighboring vertex
                temp_tri[temp_tri == vertex_index] = vert_i

                # Measure of distortion is the mean value of the variance
                # of the internal angles of the new triangles resulting
                # from the deletion of the vertex.
                dist_measure[j] = np.mean(
                    [
                        np.var(angles_triangle(i[0], i[1], i[2]))
                        for i in temp_trimesh.vertlist[temp_tri]
                    ]
                )

            # indexes of the neighboring vertices, sorted in ascending order
            # by distortion measure
            neighbor_vert_sort_dist = neighbor_vert[np.argsort(dist_measure)]

            # determine the index of the neighbor vertex with least
            # distortion that has exactly two neighbors in common with the
            # vertex to be deleted
            neighbor_vert_sel = next(
                x
                for x in neighbor_vert_sort_dist
                if len(np.intersect1d(neighbor_vert, temp_trimesh.one_ring_neighborhood(x))) == 2
            )

            # remove the two triangles, which contain both vertices
            temp_trimesh.trilist = temp_trimesh.trilist[
                np.logical_not(
                    np.logical_and(
                        (temp_trimesh.trilist == vertex_index).any(axis=1),
                        (temp_trimesh.trilist == neighbor_vert_sel).any(axis=1),
                    )
                )
            ]

            # the selected neighbor vertex replaces the vertex to be deleted
            temp_trimesh.trilist = np.where(
                temp_trimesh.trilist == vertex_index, neighbor_vert_sel, temp_trimesh.trilist
            )

            # if the vertex to be deleted is located on the boundary of the
            # triangle mesh, insert a new triangle.
            if neighbor_vert[type_of_edges == 1].any():
                temp_trimesh.trilist = np.concatenate(
                    (
                        temp_trimesh.trilist,
                        [np.append(neighbor_vert[type_of_edges == 1], neighbor_vert_sel)],
                    )
                )

            # remove vertex from vertex list
            temp_trimesh.vertlist = np.delete(temp_trimesh.vertlist, vertex_index, 0)

            # adjust indices of the triangle list
            temp_trimesh.trilist = np.where(
                temp_trimesh.trilist < vertex_index, temp_trimesh.trilist, temp_trimesh.trilist - 1
            )

        # return the mesh without the vertices to be deleted
        return temp_trimesh

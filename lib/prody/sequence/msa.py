# -*- coding: utf-8 -*-
# ProDy: A Python Package for Protein Dynamics Analysis
# 
# Copyright (C) 2010-2012 Ahmet Bakan
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#  
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

"""This module defines MSA analysis functions."""

__author__ = 'Ahmet Bakan'
__copyright__ = 'Copyright (C) 2010-2012 Ahmet Bakan'

from numpy import all, zeros, dtype, array, char, fromstring

from .msafile import splitLabel, MSAFile 

__all__ = ['MSA']

class MSA(object):
    
    """Store and manipulate multiple sequence alignments.
    
    >>> from prody import *
    >>> msafile = fetchPfamMSA('piwi', alignment='seed')
    >>> msa = parseMSA(msafile)
    >>> msa
    <MSA: piwi_seed (20 sequences, 404 residues)>

    *Querying*
    
    You can query whether a sequence in contained in the instance using
    the UniProt identifier of the sequence as follows:
        
    >>> 'YQ53_CAEEL' in msa
    True
    
    *Indexing and slicing*
    
    Retrieve a sequence at a given index:
    
    >>> msa[0] # doctest: +ELLIPSIS
    ('YQ53_CAEEL', 'DIL...YK', 650, 977)
    
    Retrieve a sequence by UniProt ID:
    
    >>> msa['YQ53_CAEEL'] # doctest: +ELLIPSIS
    ('YQ53_CAEEL', 'DIL...YK', 650, 977)
    
    Slice an MSA instance:
    
    >>> msa[:2]
    <MSA: piwi_seed' (2 sequences, 404 residues)>
    
    Slice using a list of UniProt IDs:
    
    >>> msa[:2] == msa[['YQ53_CAEEL', 'Q21691_CAEEL']]
    True
    
    Retrieve a character or a slice of a sequence:

    >>> msa[0,0]
    'D'
    >>> msa[0,0:10]
    'DILVGIAR.E'
    
    Slice MSA rows and columns:
    
    >>> msa[:10,20:40]
    <MSA: piwi_seed' (10 sequences, 20 residues)>
    
    *Refinement*
    
    Columns in an MSA that are gaps for a given sequence can be eliminated
    from the data as follows:
        
    >>> msa[:, 'YQ53_CAEEL'] # doctest: +ELLIPSIS
    <MSA: piwi_seed' (20 sequences, 328 residues)>
    
    This operation removed 76 columns, which is the number of gaps in sequence
    with label ``'YQ53_CAEEL'``.
    
    *Selective parsing*
    
    Filtering and slicing available to :class:`.MSAFile` class can be used to 
    parse an MSA selectively, which may be useful in low memory situations:
        
    >>> msa = MSA(msafile, filter=lambda lbl, seq: 'ARATH' in lbl, 
    ...           slice=list(range(10)) + list(range(394,404)))
    >>> msa
    <MSA: piwi_seed (3 sequences, 20 residues)>

    Compare this to result from parsing the complete file:
    >>> MSA(msafile)
    <MSA: piwi_seed (20 sequences, 404 residues)>"""
    
    def __init__(self, msa, **kwargs):
        """*msa* may be an :class:`.MSAFile` instance or an MSA file in a 
        supported format."""
        
        try:
            ndim, dtype_, shape = msa.ndim, msa.dtype, msa.shape
        except AttributeError:
            try:
                numseq, lenseq = msa.numSequences, msa.numResidues
            except AttributeError:
                kwargs['split'] = False
                try:
                    msa = MSAFile(msa, **kwargs)
                except Exception as err:
                    raise TypeError('msa was not recognized ({0:s})'
                                    .format(str(err)))
            
            self._msa = []
            sappend = self._msa.append
            self._labels = []
            lappend = self._labels.append
            self._mapping = mapping = {}
            
            for i, (label, seq) in enumerate(msa):
                lappend(label)
                sappend(fromstring(seq, '|S1'))
                mapping[splitLabel(label)[0]] = i
            self._msa = array(self._msa, '|S1')
            self._title = kwargs.get('title', msa.getTitle())
        else:
            if ndim != 2:
                raise ValueError('msa.dim must be 2')
            if dtype_ != dtype('|S1'):
                raise ValueError('msa must be a character array')
            numseq = shape[0]
            self._labels = labels = kwargs.get('labels')
            if labels and len(self._labels) != numseq:
                raise ValueError('len(labels) must be equal to number of '
                                 'sequences')
            
            self._mapping = mapping = kwargs.get('mapping')
            if mapping is None and labels is not None:
                # map labels to sequence index
                self._mapping = mapping = {
                    splitLabel(label)[0]: i for i, label in enumerate(labels)
                }
                
            if labels is None:
                self._labels = [None] * numseq
                
            self._msa = msa
            self._title = kwargs.get('title', 'Unknown')
        
        
    def __str__(self):
        
        return 'MSA ' + self._title
        
    def __repr__(self):
        
        return '<MSA: {0:s} ({1:d} sequences, {2:d} residues)>'.format(
                self._title, self.numSequences(), self.numResidues())
    
    def __getitem__(self, index):
        
        try:
            length = len(index)
        except TypeError: # type(index) -> int, slice
            rows, cols = index, None
        else:
            try:
                _ = index.strip
            except AttributeError: # type(index) -> tuple, list
                try:
                    _ = index.sort
                except AttributeError: # type(index) -> tuple
                    if length == 1:
                        rows, cols = index[0], None
                    elif length == 2:
                        rows, cols = index
                    else:
                        raise IndexError('invalid index: ' + repr(index))
                else: # type(index) -> list
                    rows, cols = index, None
            else: # type(index) -> str
                rows, cols = index, None 

        try: # ('PROT_HUMAN', )
            rows = self._mapping.get(rows, rows)
        except (TypeError, KeyError):
            mapping = self._mapping
            try:
                rows = [mapping[key] for key in rows]
            except (KeyError, TypeError):
                pass

        if cols is None:
            msa = self._msa[rows]
        else:
            try:
                cols = self._mapping[cols]
            except (KeyError, TypeError):
                pass
            else:
                cols = char.isalpha(self._msa[cols])
                
            try:
                msa = self._msa[rows, cols]
            except Exception:
                raise IndexError('invalid index: ' + str(index))
            
        try:
            shape, ndim = msa.shape, msa.ndim
        except AttributeError:
            return msa
        else:
            if ndim == 0:
                return msa
            elif ndim == 1:
                if cols is None:
                    label, start, end = splitLabel(self._labels[rows])
                    return label, msa.tostring(), start, end
                else:
                    return msa.tostring()
            else:
                try:
                    labels = self._labels[rows]
                except TypeError:
                    temp = self._labels
                    labels = [temp[i] for i in rows]
                return MSA(msa, title=self._title + '\'', labels=labels) 
               
    def __iter__(self):
        
        for i, label in enumerate(self._labels):
            label, start, end = splitLabel(label)
            yield label, self._msa[i].tostring(), start, end
    
    def __contains__(self, key):
        
        try:
            return key in self._mapping
        except Exception:
            pass
        return False
    
    def __eq__(self, other):

        try:
            other = other._getArray()
        except AttributeError:
            return False
        
        try:
            return all(other == self._msa)
        except Exception:
            pass
        return False
    
    def numSequences(self):
        """Return number of sequences."""
        
        return self._msa.shape[0]

    def numResidues(self):
        """Return number of residues (or columns in the MSA)."""
        
        return self._msa.shape[1]
    
    def getTitle(self):
        """Return title of the instance."""
        
        return self._title
    
    def setTitle(self, title):
        """Set title of the instance."""
        
        self._title = str(title)
        
    def getLabel(self, index, full=False):
        """Return label of the sequence at given *index*.  Residue numbers will
        be removed from the sequence label, unless *full* is **True**."""
        
        index = self._mapping.get(index, index)
        if full:
            return self._labels[index]
        else:
            return splitLabel(self._labels[index])[0]
                
    def getResnums(self, index):
        """Return starting and ending residue numbers (:term:`resnum`) for the
        sequence at given *index*."""

        index = self._mapping.get(index, index)
        return splitLabel(self._labels[index])[1:]
    
    def getArray(self):
        """Return a copy of the MSA character array."""
        
        return self._msa.copy()
    
    def _getArray(self):
        """Return MSA character array."""
        
        return self._msa
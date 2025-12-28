from typing import Callable as _Callable, Union as _Union, overload as _overload
from abc import ABC as _ABC, abstractmethod as _absd
class IMultivector(_ABC):
 @property
 @_absd
 def algebra(self) -> 'GA':
  """a reference to the Multivector's parent GA.""" 
 @_absd
 def __add__(self, other: _Union[int, float, 'IMultivector']) -> 'IMultivector':
  pass
 @_absd
 def __radd__(self, other: _Union[int, float, 'IMultivector']) -> 'IMultivector':
  pass
 @_absd
 def __sub__(self, other: _Union[int, float, 'IMultivector']) -> 'IMultivector':
  pass
 @_absd
 def __rsub__(self, other: _Union[int, float, 'IMultivector']) -> 'IMultivector':
  pass
 @_absd
 def __neg__(self) -> 'IMultivector':
  pass
 @_absd
 def __invert__(self) -> 'IMultivector':
  """Return the adjugate of the Multivector.""" 
 @_absd
 def __mul__(self, other: _Union[int, float, 'IMultivector']) -> 'IMultivector':
  """Compute e^M either by decomposing the Multivector into commuting blocks or, if that fails, explicit Taylor expansion.""" 
 @_absd
 def __rmul__(self, other: int | float) -> 'IMultivector':
  pass
 @_absd
 def __pow__(self, other: int | float) -> 'IMultivector':
  pass
 @_absd
 def __rpow__(self, other: int | float) -> 'IMultivector':
  """Exponentiate the Multivector by applying e^(M ln b).""" 
 @_absd
 def __abs__(self) -> float:
  """Return the determinant of the Multivector.""" 
 @_absd
 def __matmul__(self, grade: int) -> 'IMultivector':
  """Extract a specific grade of the Multivector.""" 
 @_absd
 def __truediv__(self, other: _Union[int, float, 'IMultivector']) -> 'IMultivector':
  pass
 @_absd
 def __rtruediv__(self, other: int | float) -> 'IMultivector':
  pass
 @_absd
 def __or__(self, other: _Union[int, float, 'IMultivector']) -> 'IMultivector':
  """Return the Perwass dot product of two Multivectors.""" 
 @_absd
 def __ror__(self, other: int | float) -> 'IMultivector':
  """Return the Perwass dot product of two Multivectors.""" 
 @_absd
 def __xor__(self, other: _Union[int, float, 'IMultivector']) -> 'IMultivector':
  """Return the wedge product of two Multivectors.""" 
 @_absd
 def __rxor__(self, other: int | float) -> 'IMultivector':
  """Return the wedge product of two Multivectors.""" 
 @_absd
 def __pos__(self) -> int | None:
  """Return the grade of the Multivector if it's a blade, None otherwise.""" 
 @_absd
 def __format__(self, form: str) -> str:
  pass
 @_absd
 def __str__(self) -> str:
  pass
 @_absd
 def __float__(self) -> float:
  """Convert a scalar Multivector to a float.""" 
 @_absd
 def __int__(self) -> float:
  """Convert a scalar Multivector to an int.""" 
 @_absd
 def exp(self) -> 'IMultivector':
  pass
 
class NoAdjugateError(ValueError):
 """Raised when a Multivector does not admit an adjugate.""" 
class GAMismatchError(TypeError):
 """Raised when two Multivectors from different GA instances are combined.""" 
_subscripts = str.maketrans('0123456789','₀₁₂₃₄₅₆₇₈₉')
def _merge_sort_parity(arr):
 if len(arr) <= 1 : return arr, 1
 mid = len(arr) // 2
 left, p_left = _merge_sort_parity(arr[:mid])
 right, p_right = _merge_sort_parity(arr[mid:])
 merged = []
 parity = p_left * p_right
 i = j = 0
 while i < len(left) and j < len(right):
  if left[i] <= right[j]:
   merged.append(left[i])
   i += 1
   continue
  merged.append(right[j])
  j += 1
  if (len(left) - i) & 1: parity = -parity
 merged.extend(left[i:])
 merged.extend(right[j:])
 return merged, parity
class GA:
 """
    A container representing a Geometric Algebra.

    Attributes:
        signature: a Callable returning the square of the nth basis vector.
        epsilon_order: integer offset for machine epsilon comparisons.
                       The effective bound for treating numbers as zero is
                       2^epsilon_order times the machine epsilon.
    """
 __slots__ = ('signature', 'epsilon_order', '__Multivector')
 signature: _Callable[[int], float]
 epsilon_order: int
 def __init__(ga, *, signature:_Callable[[int], float]= lambda x:1.0, epsilon_order:int=0):
  """
        Create a Geometric Algebra.

        Args:
            signature: a Callable returning the square of the nth basis vector.
                       Defaults to 1 for all.
            epsilon_order: integer offset for machine epsilon comparisons.
                       The effective bound for treating numbers as zero is
                       2^-epsilon_order times the machine epsilon. Defaults to 0.
        """
  ga.signature = signature
  ga.epsilon_order = epsilon_order
  class Multivector(IMultivector):
   @property
   def algebra(self) -> GA : return ga
   __slots__ = ('__d', '__decomposition', '__sigma')
   def __init__(self, keys:dict[int, float], **argv) -> None:
    from math import ldexp
    self.__d = {k:v for k, v in keys.items() if 1+abs(ldexp(v,-self.algebra.epsilon_order)) != 1}
    self.__decomposition = argv.get("decomposition", ...)
    self.__sigma = argv.get("sigma", ...)
   def __add__(self, other: _Union[int, float, 'Multivector']) -> 'Multivector':
    if isinstance(other, int | float) : return Multivector({0: self.__d.get(0, 0) + other,**{mask: value for mask, value in self.__d.items() if mask != 0}},decomposition=self.__decomposition, sigma=self.__sigma)
    if not isinstance(other, Multivector):
     if isinstance(other, IMultivector): raise GAMismatchError("Cannot combine Multivectors from different GA instances")
     return NotImplemented
    return Multivector({mask: self.__d.get(mask, 0) + other._Multivector__d.get(mask, 0) for mask in sorted(self.__d.keys() | other._Multivector__d.keys())})
   def __radd__(self, other: _Union[int, float, 'Multivector']) -> 'Multivector' : return self+other
   def __sub__(self, other: _Union[int, float, 'Multivector']) -> 'Multivector' : return self+(-other)
   def __rsub__(self,other: _Union[int, float, 'Multivector']) -> 'Multivector': return -self+other
   def __neg__(self) -> 'Multivector' : return Multivector({mask: -val for mask, val in self.__d.items()}, decomposition=self.__decomposition)
   def __invert__(self) -> 'Multivector':
    sigma = self.__get_sigma()
    return Multivector({k: -v if (sigma >> n)&1 else v for n, (k, v) in enumerate(self.__d.items())},decomposition=self.__decomposition)
   def __rmul__(self, other: int | float) -> 'Multivector':
    if isinstance(other, int | float) : return self*other
    return NotImplemented
   def __pow__(self, other: int | float) -> 'Multivector':
    if not isinstance(other, int | float) : return NotImplemented
    from math import ldexp
    if 1 + abs(ldexp(other % 1, -self.algebra.epsilon_order)) != 1: raise ValueError(f'Multivector exponent must be an integer, but got {other}')
    other = int(round(other))
    if other == 0 : return self.algebra[0]
    if other < 0:
     if det := abs(self): out = (~self)/det
     else: raise ZeroDivisionError(f"Cannot invert {self}: determinant is zero")
    else: out = self
    for _ in range(abs(other)-1): out *= self
    return out
   def __abs__(self) -> float : return (self*~self)._Multivector__d.get(0, 0)
   def __get_sigma(self):
    if self.__sigma is None: raise NoAdjugateError(f'Adjugate undefined for {self}')
    if self.__sigma is not ... : return self.__sigma
    blades = list(self.__d.keys())
    if len(blades) == 0:
     self.__sigma = 0
     return 0
    if added := blades[0] != 0: blades = [0] + blades
    from collections import deque
    n = len(blades)
    epsilon = [[0]*n for _ in range(n)]
    for i in range(n):
     for j in range(n):
      t = (blades[i] & blades[j]).bit_count()
      parity = (blades[i].bit_count()*blades[j].bit_count() - t) & 1
      epsilon[i][j] = -1 if parity else +1
     
    sigma = 0
    known = 1
    queue = deque([0])
    while queue:
     i = queue.popleft()
     si = -1 if (sigma >> i) & 1 else +1
     for j in range(n):
      if i == j: continue
      required_sign = -epsilon[i][j] * si
      required_bit = 1 if required_sign == -1 else 0
      mask = 1 << j
      if not (known & mask):
       if required_bit: sigma |= mask
       else: sigma &= ~mask
       known |= mask
       queue.append(j)
       continue
      current_bit = (sigma >> j) & 1
      if current_bit != required_bit:
       if +(self*(2*self@0-self)) == 0:
        self.__sigma = sum(1 << n for n, b in enumerate(blades) if b != 0)
        if added: self.__sigma >>= 1
        return self.__sigma
       self.__sigma = None
       raise NoAdjugateError(f'Adjugate undefined for {self}')
      
     
    return sigma >> 1 if added else sigma
   def __rpow__(self, other: int | float) -> 'Multivector':
    if not isinstance(other, int | float) : return NotImplemented
    import math
    return (math.log(other)*self).exp()
   def __mulbases(self, mask1, mask2):
    if mask1 == 0 : return mask2, 1
    if mask2 == 0 : return mask1, 1
    if mask1 == mask2:
     init = -1 if mask1.bit_count() % 4 >= 2 else 1
     for n in range(mask1.bit_length()):
      if (mask1 >> n) & 1: init *= self.algebra.signature(n+1)
     return 0, init
    val = 1
    bases = [i for i in range(mask1.bit_length()) if (mask1 >> i) & 1] + [i for i in range(mask2.bit_length()) if (mask2 >> i) & 1]
    seen = set()
    for basis in tuple(bases):
     if basis in seen: continue
     seen.add(basis)
     diff = 0
     keep = False
     for n, factor in enumerate(reversed(tuple(bases))):
      if factor != basis: continue
      keep = not keep
      if keep:
       diff = n
       continue
       
      if n % 2 == diff % 2: val *= -1
      bases.pop(~diff)
      bases.pop(~n+1 if n>diff else ~n)
      val *= self.algebra.signature(basis+1)
      
     
    bases, parity = _merge_sort_parity(bases)
    bases = sum(1 << i for i in bases)
    return bases, val*parity
   def __or__(self, other: _Union[int, float, 'Multivector']) -> 'Multivector':
    if isinstance(other, int | float) : return self*other
    if not isinstance(other, Multivector):
     if isinstance(other, IMultivector): raise GAMismatchError("Cannot combine Multivectors from different GA instances")
     return NotImplemented
    new = {}
    for mask1, val1 in self.__d.items():
     for mask2, val2 in other._Multivector__d.items():
      if (mask1^mask2).bit_count() != abs(mask1.bit_count() - mask2.bit_count()): continue
      mask, basisprod = self.__mulbases(mask1, mask2)
      new[mask] = new.get(mask, 0) + val1*val2*basisprod
     
    return Multivector(dict(sorted(new.items())))
   def __ror__(self, other: int | float) -> 'Multivector':
    if not isinstance(other, int | float) : return NotImplemented
    return self*other
   def __xor__(self, other: _Union[int, float, 'Multivector']) -> 'Multivector':
    if isinstance(other, int | float) : return self.algebra[-1]
    if not isinstance(other, Multivector):
     if isinstance(other, IMultivector): raise GAMismatchError("Cannot combine Multivectors from different GA instances")
     return NotImplemented
    new = {}
    for mask1, val1 in self.__d.items():
     for mask2, val2 in other._Multivector__d.items():
      if (mask1^mask2).bit_count() != mask1.bit_count() + mask2.bit_count(): continue
      mask, basisprod = self.__mulbases(mask1, mask2)
      new[mask] = new.get(mask, 0) + val1*val2*basisprod
     
    return Multivector(dict(sorted(new.items())))
   def __rxor__(self, other: int | float) -> 'Multivector':
    if not isinstance(other, int | float) : return NotImplemented
    return self.algebra[-1]
   def __mul__(self, other: _Union[int, float, 'Multivector']) -> 'Multivector':
    from math import ldexp
    if isinstance(other, int | float) : return Multivector({mask: other*val for mask, val in self.__d.items()},decomposition=self.__decomposition, sigma=self.__sigma)if 1+abs(ldexp(other, -self.algebra.epsilon_order)) != 1else Multivector({})
    elif not isinstance(other, Multivector):
     if isinstance(other, IMultivector): raise GAMismatchError("Cannot combine Multivectors from different GA instances")
     return NotImplemented
    new = {}
    for mask1, val1 in self.__d.items():
     for mask2, val2 in other._Multivector__d.items():
      mask, basisprod = self.__mulbases(mask1, mask2)
      new[mask] = new.get(mask, 0) + val1*val2*basisprod
     
    return Multivector(dict(sorted(new.items())))
   def __matmul__(self, grade: int) -> 'Multivector':
    if not isinstance(grade, int) : return NotImplemented
    return Multivector({mask: val for mask, val in self.__d.items() if mask.bit_count() == grade})
   def __decompose(self):
    if self.__decomposition is not ... : return self.__decomposition
    commutes = lambda mask1,mask2: mask1.bit_count()*mask2.bit_count()%2 == (mask1&mask2).bit_count()%2
    blocks = []
    for mask in self.__d.keys():
     noncom = 0
     noncomindex = None
     for n, block in enumerate(blocks):
      comtrack = None
      for item in block:
       if comtrack is None:
        comtrack = commutes(mask, item)
        continue
       if comtrack is not commutes(mask, item):
        if +(self*self) == 0:
         self.__decomposition = NotImplemented
         return NotImplemented
        self.__decomposition = None
        return None
       
      if comtrack is False:
       noncomindex = n
       noncom+=1
      
     if noncom == 0: blocks.append([mask])
     elif noncom == 1: blocks[noncomindex].append(mask)
     else:
      self.__decomposition = None
      return None
     
    self.__decomposition = blocks
    return blocks
   def exp(self) -> 'Multivector':
    d = self.__decompose()
    if d is None:
     from math import ldexp
     current = self
     cumulus = self.algebra[0] + current
     n = 2
     while True:
      current *= self
      current /= n
      if 1+abs(ldexp(sum(s*s for s in current.__d.values()),-self.algebra.epsilon_order)) == 1: break
      cumulus += current
      n+=1
     return cumulus
    import math
    if d is NotImplemented:
     if (s := (self|self).__d.get(0,0)) != 0: value = math.sqrt(abs(s))
     return self.algebra[0]*math.cosh(value) + self*math.sinh(value)/value if s > 0else self.algebra[0] + self if s == 0else self.algebra[0]*math.cos(value) + self*math.sin(value)/value
    prod = 1.0
    for block in d:
     if block == [0]:
      prod *= math.exp(self.__d[0])
      continue
     total = 0
     for mask in block:
      norm = -1 if mask.bit_count() % 4 >= 2 else 1
      for i in range(mask.bit_length()):
       if (mask >> i) & 1: norm *= self.algebra.signature(i+1)
       
      total += norm * self.__d[mask]**2
     if total != 0: value = math.sqrt(abs(total))
     prod *= Multivector({0: math.cosh(value), **{mask:math.sinh(value)*self.__d[mask]/value for mask in block}})if total > 0else Multivector({0: 1, **{mask: self.__d[mask] for mask in block}})if total == 0else Multivector({0: math.cos(value), **{mask:math.sin(value)*self.__d[mask]/value for mask in block}})
    return prod if isinstance(prod, Multivector) else Multivector({0: prod})
   def __pos__(self) -> int | None:
    grade = None
    for mask in self.__d.keys():
     if grade is None: grade = mask.bit_count()
     elif mask.bit_count() != grade : return None
    return grade
   def __truediv__(self, other: _Union[int, float, 'Multivector']) -> 'Multivector':
    if isinstance(other, int | float) : return Multivector({mask: value/other for mask, value in self.__d.items()},decomposition=self.__decomposition, sigma=self.__sigma)
    if not isinstance(other, Multivector):
     if isinstance(other, IMultivector): raise GAMismatchError("Cannot combine Multivectors from different GA instances")
     return NotImplemented
    return self*(other**(-1))
   def __rtruediv__(self, other: int | float) -> 'Multivector':
    if not isinstance(other, int | float) : return NotImplemented
    return other*(self**(-1))
   def __format__(self, form: str) -> str : return '<'+(''.join(('+' if value > 0 else '') + format(value, form) + ''.join('e' + str(i+1).translate(_subscripts) for i in range(mask.bit_length()) if (mask >> i) & 1)for mask, value in self.__d.items()).removeprefix('+') if self.__d else format(0.0,form))+'>'
   def __str__(self) -> str : return f'{self:g}'
   def __float__(self) -> float:
    if (l := len(self.__d)) == 0 : return 0.0
    elif l == 1 and 0 in self.__d : return self.__d[0]
    raise ValueError(f"Cannot convert to float: Multivector is not a scalar")
   def __int__(self) -> int:
    if (l := len(self.__d)) == 0 : return 0
    elif l == 1 and 0 in self.__d : return int(self.__d[0])
    raise ValueError(f"Cannot convert to int: Multivector is not a scalar")
   
  ga.__Multivector = Multivector
 @_overload
 def __getitem__(self, n: int) -> IMultivector:
  pass
 @_overload
 def __getitem__(self, n: slice) -> tuple[IMultivector]:
  pass
 def __getitem__(self, n):
  """
        Get the nth basis vector of the GA if n > 1, the unit scalar if n = 0
        and the zero Multivector if n < 0.
        """
  if isinstance(n, int) : return self.__Multivector({(1<<(n-1) if n > 0 else 0): 1.0} if n >= 0 else {})
  if not isinstance(n, slice) : return NotImplemented
  if n.stop is None: raise ValueError('Cannot create an open-ended slice of GA; please specify a finite stop index.')
  step = n.step or 1
  start = n.start or 0
  return tuple(self[n] for n in range(start, n.stop, step))
 def __call__(self, multivector: IMultivector) -> IMultivector:
  """
        Convert any Multivector to a Multivector of this GA.
        """
  return self.__Multivector(multivector._Multivector__d,decomposition=multivector._Multivector__decomposition,sigma=multivector._Multivector__sigma)
 def __str__(self) -> str : return f"GA<signature={getattr(self.signature, '__name__', repr(self.signature))}, epsilon_order={self.epsilon_order}>"


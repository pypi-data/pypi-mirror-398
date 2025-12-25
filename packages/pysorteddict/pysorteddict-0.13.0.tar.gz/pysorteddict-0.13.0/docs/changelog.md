# Changelog

## [0.13.0](https://github.com/tfpf/pysorteddict/compare/v0.12.1...v0.13.0)

<ul class="change-new">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/224">#224</a> Provide built distributions for the GIL-enabled
  build of Python 3.14.</li>
  <li><a href="https://github.com/tfpf/pysorteddict/pull/230">#230</a> Support <code>datetime.date</code>,
  <code>datetime.timedelta</code>, <code>fractions.Fraction</code>, <code>ipaddress.IPv4Address</code>,
  <code>ipaddress.IPv4Interface</code>, <code>ipaddress.IPv4Network</code>, <code>ipaddress.IPv6Address</code>,
  <code>ipaddress.IPv6Interface</code>, <code>ipaddress.IPv6Network</code>, <code>pathlib.PosixPath</code>,
  <code>pathlib.PurePosixPath</code>, <code>pathlib.PureWindowsPath</code>, <code>pathlib.WindowsPath</code>,
  <code>time.struct_time</code> and <code>uuid.UUID</code> keys.</li>
  <li><a href="https://github.com/tfpf/pysorteddict/pull/235">#235</a> Provide built distributions for the GIL-disabled
  build of Python 3.14 on Linux and macOS.</li>
  <li><a href="https://github.com/tfpf/pysorteddict/pull/234">#234</a> Provide a built distribution for the
  GIL-disabled build of Python 3.14 on Windows.</li>
  <li><a href="https://github.com/tfpf/pysorteddict/pull/239">#239</a> Provide built distributions for the Pyodide
  build of Python 3.12 and 3.13.</li>
</ul>

## [0.12.1](https://github.com/tfpf/pysorteddict/compare/v0.12.0...v0.12.1)

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/219">#219</a> Allow using a sorted dictionary even if
  importing <code>decimal.Decimal</code> fails.</li>
</ul>

## [0.12.0](https://github.com/tfpf/pysorteddict/compare/v0.11.0...v0.12.0)

<ul class="change-new">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/210">#210</a> Define
  <code>SortedDictItems.__reversed__</code>. Define <code>SortedDictItemsRevIter</code> as a reverse iterator over the
  values of a sorted dictionary. Define <code>SortedDictItemsRevIter.__next__</code>. Define
  <code>SortedDictKeys.__reversed__</code> and <code>SortedDict.__reversed__</code>. Define
  <code>SortedDictKeysRevIter</code> as a reverse iterator over the keys of a sorted dictionary. Define
  <code>SortedDictKeysRevIter.__next__</code>. Define <code>SortedDictValues.__reversed__</code>. Define
  <code>SortedDictValuesRevIter</code> as a reverse iterator over the values of a sorted dictionary. Define
  <code>SortedDictValuesRevIter.__next__</code>.</li>
</ul>

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/205">#205</a> Add homepage build dependencies to project
  metadata.</li>
</ul>

<ul class="change-break">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/211">#211</a> Rename <code>SortedDictItemsIter</code> to
  <code>SortedDictItemsFwdIter</code>, <code>SortedDictKeysIter</code> to <code>SortedDictKeysFwdIter</code> and
  <code>SortedDictValuesIter</code> to <code>SortedDictValuesFwdIter</code>.</li>
</ul>

## [0.11.0](https://github.com/tfpf/pysorteddict/compare/v0.10.0...v0.11.0)

<ul class="change-new">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/196">#196</a> Define <code>SortedDict.get</code> to return the
  value mapped to a key or a specified default.</li>
  <li><a href="https://github.com/tfpf/pysorteddict/pull/198">#198</a> Define <code>SortedDict.setdefault</code> to
  return the value mapped to a key or a specified default and map that default to the key.</li>
</ul>

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/commit/8fe14d796917482f830af5921d5b18546a9d7843">8fe14d796917</a>
  Add optional testing dependencies to project metadata.</li>
  <li><a href="https://github.com/tfpf/pysorteddict/pull/197">#197</a> Define
  <code>SortedDictItems.__contains__</code>.</li>
</ul>

## [0.10.0](https://github.com/tfpf/pysorteddict/compare/v0.9.0...v0.10.0)

<ul class="change-new">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/184">#184</a> Define <code>SortedDictValues</code> as a view
  over the values of a sorted dictionary. Define <code>SortedDictValues.__repr__</code>,
  <code>SortedDictValues.__len__</code>, <code>SortedDictValues.__getitem__</code> and
  <code>SortedDictValues.__iter__</code>. Define <code>SortedDictValuesIter</code> as an iterator over the values of a
  sorted dictionary. Define <code>SortedDictValuesIter.__iter__</code> and <code>SortedDictValuesIter.__next__</code>.
  Update <code>SortedDict.values</code> to return the aforementioned view.</li>
  <li><a href="https://github.com/tfpf/pysorteddict/pull/187">#187</a> Define <code>SortedDictItems</code> as a view
  over the items of a sorted dictionary. Define <code>SortedDictItems.__repr__</code>,
  <code>SortedDictItems.__len__</code>, <code>SortedDictItems.__getitem__</code> and
  <code>SortedDictItems.__iter__</code>. Define <code>SortedDictItemsIter</code> as an iterator over the items of a
  sorted dictionary. Define <code>SortedDictItemsIter.__iter__</code> and <code>SortedDictItemsIter.__next__</code>.
  Update <code>SortedDict.items</code> to return the aforementioned view.</li>
</ul>

## [0.9.0](https://github.com/tfpf/pysorteddict/compare/v0.8.2...v0.9.0)

<ul class="change-new">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/179">#179</a> Define <code>SortedDict.__iter__</code>.</li>
</ul>

## [0.8.2](https://github.com/tfpf/pysorteddict/compare/v0.8.1...v0.8.2)

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/175">#175</a> Update <code>SortedDictKeys.__getitem__</code>
  to speed up the creation of a positive slice near the end or a negative slice near the beginning.</li>
</ul>

## [0.8.1](https://github.com/tfpf/pysorteddict/compare/v0.8.0...v0.8.1)

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/169">#169</a> Update <code>SortedDictKeys.__getitem__</code>
  to raise the same errors <code>list.__getitem__</code> raises.</li>
</ul>

## [0.8.0](https://github.com/tfpf/pysorteddict/compare/v0.7.3...v0.8.0)

<ul class="change-new">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/163">#163</a> Define
  <code>SortedDictKeys.__getitem__</code>.</li>
</ul>

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/164">#164</a> Update <code>SortedDict.__len__</code> to raise
  <code>OverflowError</code> if the length exceeds the maximum value a <code>Py_ssize_t</code> can have.</li>
</ul>

## [0.7.3](https://github.com/tfpf/pysorteddict/compare/v0.7.2...v0.7.3)

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/149">#149</a> Exclude test files from the source distribution.
  Exclude source files from the built distributions.</li>
  <li><a href="https://github.com/tfpf/pysorteddict/pull/157">#157</a> Define
  <code>SortedDictKeys.__contains__</code>.</li>
</ul>

## [0.7.2](https://github.com/tfpf/pysorteddict/compare/v0.7.1...v0.7.2)

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/141">#141</a> Add changelog link to project metadata.</li>
</ul>

## [0.7.1](https://github.com/tfpf/pysorteddict/compare/v0.7.0...v0.7.1)

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/131">#131</a> Allow most modifications to a sorted dictionary
  while iterating over its keys. Prohibit deleting the key any iterator is about to yield next. Prohibit clearing the
  sorted dictionary when any unexhausted iterators exist.</li>
</ul>

## [0.7.0](https://github.com/tfpf/pysorteddict/compare/v0.6.0...v0.7.0)

<ul class="change-new">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/120">#120</a> Define <code>SortedDictKeys</code> as a view
  over the keys of a sorted dictionary. Define <code>SortedDictKeys.__repr__</code>,
  <code>SortedDictKeys.__len__</code> and <code>SortedDictKeys.__iter__</code>. Define <code>SortedDictKeysIter</code>
  as an iterator over the keys of a sorted dictionary. Define <code>SortedDictKeysIter.__iter__</code> and
  <code>SortedDictKeysIter.__next__</code>. Update <code>SortedDict.keys</code> to return the aforementioned view.
  Prohibit modifications to a sorted dictionary while iterating over its keys.</li>
</ul>

## [0.6.0](https://github.com/tfpf/pysorteddict/compare/v0.5.3...v0.6.0)

<ul class="change-break">
  <li><a href="https://github.com/tfpf/pysorteddict/commit/84830cb2d98afa28a1be188f42da5938080a5435">84830cb2d98a</a>
  Update the check for the import of <code>decimal.Decimal</code> with type verification. Change the error message to
  reflect that importing the type failed.</li>
  <li><a href="https://github.com/tfpf/pysorteddict/pull/118">#118</a> Update <code>SortedDict.__contains__</code> to
  raise the same errors <code>SortedDict.__getitem__</code> raises (excluding <code>KeyError</code>) instead of
  silently returning <code>False</code>.</li>
</ul>

## [0.5.3](https://github.com/tfpf/pysorteddict/compare/v0.5.2...v0.5.3)

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/commit/61c6d76c88c2849bed2c092afe2aeb7349bd33bf">61c6d76c88c2</a>
  Add GitHub links to project metadata.</li>
</ul>

## [0.5.2](https://github.com/tfpf/pysorteddict/compare/v0.5.1...v0.5.2)

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/commit/6bf7bbdef8cbc83d64d57e2eb50b2c3a5146a63b">6bf7bbdef8cb</a>
  Remove GitHub links from project metadata.</li>
  <li><a href="https://github.com/tfpf/pysorteddict/pull/111">#111</a> Change the error message about failure to import
  Python types which are not built-in to report the problem more precisely.</li>
</ul>

## [0.5.1](https://github.com/tfpf/pysorteddict/compare/v0.5.0...v0.5.1)

No user-facing changes of note.

## [0.5.0](https://github.com/tfpf/pysorteddict/compare/v0.4.6...v0.5.0)

<ul class="change-new">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/102">#102</a> Support <code>decimal.Decimal</code> keys.
  Prohibit the insertion of a key if it is NaN.</li>
</ul>

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/commit/8c145e38eb98d623a640521ec996d49cc1af90fd">8c145e38eb98</a>
  Add GitHub and homepage links to project metadata.</li>
</ul>

## [0.4.6](https://github.com/tfpf/pysorteddict/compare/v0.4.5...v0.4.6)

No user-facing changes of note.

## [0.4.5](https://github.com/tfpf/pysorteddict/compare/v0.4.4...v0.4.5)

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/95">#95</a> Change the type of the error raised when the key
  type is not set from <code>ValueError</code> to <code>RuntimeError</code>. Add documentation link to project
  metadata.</li>
</ul>

## [0.4.4](https://github.com/tfpf/pysorteddict/compare/v0.4.3...v0.4.4)

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/91">#91</a> Change error messages to provide actionable
  information.</li>
</ul>

## [0.4.3](https://github.com/tfpf/pysorteddict/compare/v0.4.2...v0.4.3)

No user-facing changes of note.

## [0.4.2](https://github.com/tfpf/pysorteddict/compare/v0.4.1...v0.4.2)

No user-facing changes of note.

## [0.4.1](https://github.com/tfpf/pysorteddict/compare/v0.4.0...v0.4.1)

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/75">#75</a> Include the C++ header files from the project in
  the source and built distributions.</li>
</ul>

## [0.4.0](https://github.com/tfpf/pysorteddict/compare/v0.3.0...v0.4.0)

<ul class="change-new">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/67">#67</a> Support <code>float</code> keys. Prohibit the
  insertion of a key if it is NaN.</li>
  <li><a href="https://github.com/tfpf/pysorteddict/pull/71">#71</a> Define <code>SortedDict.key_type</code> as the key
  type of a sorted dictionary.</li>
</ul>

## [0.3.0](https://github.com/tfpf/pysorteddict/compare/v0.2.1...v0.3.0)

<ul class="change-new">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/55">#55</a> Support <code>bytes</code> and <code>str</code>
  keys.
</ul>

<ul class="change-break">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/47">#47</a> Update the <code>SortedDict</code> constructor to
  ignore all arguments. Update <code>SortedDict.__setitem__</code> to set the key type upon succeeding the first
  time.</li>
  <li><a href="https://github.com/tfpf/pysorteddict/pull/49">#49</a> Remove <code>SortedDict.__str__</code>. Define
  <code>SortedDict.__repr__</code>.</li>
</ul>

## [0.2.1](https://github.com/tfpf/pysorteddict/compare/v0.2.0...v0.2.1)

No user-facing changes of note.

## [0.2.0](https://github.com/tfpf/pysorteddict/compare/v0.1.0...v0.2.0)

<ul class="change-new">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/36">#36</a> Define <code>SortedDict.copy</code> to return a
  shallow copy of a sorted dictionary.</li>
</ul>

## [0.1.0](https://github.com/tfpf/pysorteddict/compare/v0.0.8...v0.1.0)

<ul class="change-new">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/29">#29</a> Define <code>SortedDict.__contains__</code>.</li>
  <li><a href="https://github.com/tfpf/pysorteddict/pull/31">#31</a> Define <code>SortedDict.clear</code> to remove all
  key-value pairs from a sorted dictionary.</li>
</ul>

## [0.0.8](https://github.com/tfpf/pysorteddict/compare/v0.0.7...v0.0.8)

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/pull/22">#22</a> Change the type of the error raised when the
  constructor argument is an unsupported type from <code>ValueError</code> to <code>TypeError</code>. Prohibit
  subclasses of supported key types. Update <code>SortedDict.__str__</code> and <code>SortedDict.items</code> to raise
  allocation errors.</li>
</ul>

## [0.0.7](https://github.com/tfpf/pysorteddict/compare/v0.0.6...v0.0.7)

<ul class="change-fix">
  <li><a href="https://github.com/tfpf/pysorteddict/commit/e377dc4266f683daba99427e4955c3065d5f63a3">e377dc4266f6</a>
  Add intended audience, supported operating systems and targeted Python implementations to project metadata.</li>
</ul>

## [0.0.6](https://github.com/tfpf/pysorteddict/compare/v0.0.5...v0.0.6)

No user-facing changes of note.

## [0.0.5](https://github.com/tfpf/pysorteddict/compare/v0.0.4...v0.0.5)

No user-facing changes of note.

## 0.0.4

<ul class="change-new">
  <li><a href="https://github.com/tfpf/pysorteddict/commit/8ef0310913b47b1539b6524d0cf94424825c0a38">8ef0310913b4</a>
  Define <code>SortedDict</code>. Define the <code>SortedDict</code> constructor to accept the key type, which must be
  <code>int</code>.</li>
  <li><a href="https://github.com/tfpf/pysorteddict/pull/1">#1</a> Define the <code>SortedDict</code> destructor.</li>
  <li><a href="https://github.com/tfpf/pysorteddict/pull/2">#2</a> Define <code>SortedDict.__len__</code>,
  <code>SortedDict.__getitem__</code>, <code>SortedDict.__setitem__</code>, <code>SortedDict.__delitem__</code> and
  <code>SortedDict.__str__</code>. Prohibit insertion of a key if its type is not a subclass of what was passed to the
  constructor.</li>
  <li><a href="https://github.com/tfpf/pysorteddict/pull/3">#3</a> Define <code>SortedDict.items</code>,
  <code>SortedDict.keys</code> and <code>SortedDict.values</code> to return lists (not views) containing the key-value
  pairs, keys and values in a sorted dictionary.</li>
</ul>

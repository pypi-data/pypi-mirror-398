project(
    'pysorteddict',
    'cpp',
    default_options: [
        'cpp_std=c++20',
        # On Windows, MSVC must be used, but Meson uses MinGW (if available).
        # Hence, force it to use MSVC. This is harmless on other platforms. See
        # https://mesonbuild.com/meson-python/how-to-guides/meson-args.html.
        'vsenv=true',
    ]
)

source_directory = 'src' / 'pysorteddict'
source_files = files(
    source_directory / 'sorted_dict_items_type.cc',
    source_directory / 'sorted_dict_keys_type.cc',
    source_directory / 'sorted_dict_module.cc',
    source_directory / 'sorted_dict_type.cc',
    source_directory / 'sorted_dict_values_type.cc',
    source_directory / 'sorted_dict_view_type.cc',
)

py = import('python').find_installation(pure: false)
py.extension_module(
    'pysorteddict',
    source_files,
    install: true,
)

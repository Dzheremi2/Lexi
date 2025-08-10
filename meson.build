project(
    'lexi',
    version: '1.4',
    meson_version: '>= 1.0.0',
    default_options: [ 'warning_level=2', 'werror=false', ],
)

i18n = import('i18n')
gnome = import('gnome')
python = import('python')

py_installation = python.find_installation('python3')

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())

profile = get_option('profile')
if profile == 'development'
    app_id = 'io.github.dzheremi2.lexi.Devel'
    prefix = '/io/github/dzheremi2/lexi/Devel'
elif profile == 'release'
    app_id = 'io.github.dzheremi2.lexi'
    prefix = '/io/github/dzheremi2/lexi'
endif

conf = configuration_data()
conf.set('PYTHON', py_installation.full_path())
conf.set('APP_ID', app_id)
conf.set('PREFIX', prefix)
conf.set('VERSION', meson.project_version())
conf.set('CACHEV', 2)
conf.set('localedir', join_paths(get_option('prefix') / get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

subdir('data')
subdir('lexi')
subdir('po')

gnome.post_install(
    glib_compile_schemas: true,
    gtk_update_icon_cache: true,
    update_desktop_database: true
)
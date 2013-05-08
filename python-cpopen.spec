%{!?python_ver: %global python_ver %(%{__python} -c "import sys ; print sys.version[:3]")}

Name:           python-cpopen
Version:        1.2.2
Release:        1%{?dist}
Summary:        Creates a sub-process in simpler safer manner

License:        GPLv2+
Group:          System Environment/Libraries
URL:            http://pypi.python.org/pypi/cpopen
Source0:        http://pypi.python.org/packages/source/c/cpopen/cpopen-%{version}.tar.gz

BuildRequires: python2-devel

%description
Python package for creating sub-process in simpler and safer manner by using C
code.

%prep
%setup -q -n cpopen-%{version}

%build
%{__python} setup.py build


%install
%{__python} setup.py install --root $RPM_BUILD_ROOT \
                             --install-lib %{python_sitearch}

%files
%{python_sitearch}/cpopen.so*
%{python_sitearch}/__init__.py*
%{python_sitearch}/cpopen-%{version}-py*.egg-info

%attr(755, root, root) %{python_sitearch}/cpopen.so*

%changelog
* Wed May 08 2013 Yaniv Bronhaim <ybronhei@redhat.com> 1.2.2
- Merging vdsm-python-cpopen fixes

* Tue Mar 19 2013 Yaniv Bronhaim <ybronhei@redhat.com> 1.2.1
- Changing ownership and mod of cpopen-createprocess.so file

* Wed Mar 13 2013 Yaniv Bronhaim <ybronhei@redhat.com> 1.2
- Renaming createprocess to cpopen-createprocess

* Mon Feb 05 2013 Yaniv Bronhaim <ybronhei@redhat.com> 1.1
- Fix dependencies
- Adding AUTHORS file

* Sun Jan 20 2013 Yaniv Bronhaim <ybronhei@redhat.com> 1.0
- Initial take


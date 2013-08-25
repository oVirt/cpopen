%{!?python_ver: %global python_ver %(%{__python} -c "import sys ; print sys.version[:3]")}
%global __provides_exclude_from ^(%{python_sitearch}|%{python3_sitearch})/.*\\.so$

Name:           python-cpopen
Version:        1.2.3
Release:        1%{?dist}
Summary:        Creates a sub-process in simpler safer manner

License:        GPLv2+
Group:          System Environment/Libraries
URL:            http://pypi.python.org/pypi/cpopen
Source0:        http://bronhaim.fedorapeople.org/cpopen-%{version}.tar.gz

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
%doc AUTHORS COPYING MANIFEST
%{python_sitearch}/cpopen/__init__.py*
%{python_sitearch}/cpopen/cpopen-%{version}-py*.egg-info
%attr(755, root, root) %{python_sitearch}/cpopen/cpopen.so*

%changelog
* Sun Aug 25 2013 Yaniv Bronhaim <ybronhei@redhat.com> - 1.2.3
- Moving files under cpopen folder

* Wed Jun 12 2013 Yaniv Bronhaim <ybronhei@redhat.com> - 1.2.2-1
- Merging vdsm-python-cpopen fixes
- Renaming to cpopen.so

* Tue Mar 19 2013 Yaniv Bronhaim <ybronhei@redhat.com> 1.2.1-1
- Changing ownership and mod of cpopen-createprocess.so file

* Wed Mar 13 2013 Yaniv Bronhaim <ybronhei@redhat.com> 1.2-1
- Renaming createprocess to cpopen-createprocess

* Tue Feb 05 2013 Yaniv Bronhaim <ybronhei@redhat.com> 1.1-1
- Fix dependencies
- Adding AUTHORS file

* Sun Jan 20 2013 Yaniv Bronhaim <ybronhei@redhat.com> 1.0-1
- Initial take


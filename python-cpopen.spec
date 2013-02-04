%{!?python_ver: %global python_ver %(%{__python} -c "import sys ; print sys.version[:3]")}

Name:           python-cpopen
Version:        1.0
Release:        1%{?dist}
Summary:        Creates a subprocess in simpler safer manner

License:        GPLv2+
Group:          System Environment/Libraries
URL:            http://pypi.python.org/pypi/cpopen
Source0:        http://pypi.python.org/packages/source/c/cpopen/cpopen-%{version}.tar.gz

BuildRequires: python2-devel

%description
Python package for creating subprocess in simpler and safer manner by using C code.

%prep
%setup -q -n python-cpopen-%{version}

%build
%{__python} setup.py build


%install
%{__python} setup.py install --root $RPM_BUILD_ROOT --install-lib %{python_sitearch}

%files
%{python_sitearch}/createprocess.so*
%{python_sitearch}/cpopen.py*
%{python_sitearch}/cpopen-%{version}-py*.egg-info

%changelog
* Sun Jan 20 2013 Yaniv Bronhaim <ybronhei@redhat.com> 1.0
- Initial take

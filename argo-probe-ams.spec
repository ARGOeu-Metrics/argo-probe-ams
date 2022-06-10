# sitelib
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%define dir /usr/libexec/argo/probes/ams

Name: argo-probe-ams
Summary: Probes for ARGO AMS.
Version: 0.1.0
Release: 1%{?dist}
License: ASL 2.0
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Group: Network/Monitoring
BuildArch: noarch
Requires: argo-ams-library

%description
This package includes probes for ARGO AMS component.

%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf %{buildroot}
%{__python} setup.py install --skip-build --root %{buildroot} --record=INSTALLED_FILES
install -d -m 755 %{buildroot}/%{dir}
install -d -m 755 %{buildroot}/%{python_sitelib}/argo_probe_ams

%clean
rm -rf %{buildroot}

%files -f INSTALLED_FILES
%defattr(-,root,root,-)
%{python_sitelib}/argo_probe_ams
%{dir}


%changelog
* Fri Jun 10 2022 Katarina Zailac <kzailac@gmail.com> - 0.1.0-1%{?dist}
- AO-650 Harmonize argo-mon probes

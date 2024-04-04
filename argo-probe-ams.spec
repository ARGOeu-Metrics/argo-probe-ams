%define dir /usr/libexec/argo/probes/ams

Name: argo-probe-ams
Summary: Probes for ARGO AMS.
Version: 0.1.2
Release: 1%{?dist}
License: ASL 2.0
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Group: Network/Monitoring
BuildArch: noarch
Requires: python3-argo-ams-library

%description
This package includes probes for ARGO AMS component.

%prep
%setup -q

%build
%{py3_build}

%install
%{py3_install "--record=INSTALLED_FILES" }

%clean
rm -rf %{buildroot}

%files -f INSTALLED_FILES
%defattr(-,root,root,-)
%{python3_sitelib}/argo_probe_ams
%{dir}


%changelog
* Thu Apr 4 2024 Katarina Zailac <kzailac@srce.hr> - 0.1.2-1%{?dist}
- AO-922 Create Rocky 9 rpm for argo-probe-ams
* Fri Jun 10 2022 Katarina Zailac <kzailac@gmail.com> - 0.1.0-1%{?dist}
- AO-650 Harmonize argo-mon probes

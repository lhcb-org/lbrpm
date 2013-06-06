
%define project LCGCMT
%define lbversion preview
%define cmtconfig x86_64-slc6-gcc48-opt
%define LCGCMTROOT /afs/cern.ch/sw/lcg/experimental/

%define cmtconfig_rpm %( echo %{cmtconfig} | tr '-' '_' )
%define rpmversion %{lbversion}_%{cmtconfig_rpm}

%define _topdir /tmp/rpmbuild
%define tmpdir /tmp/tmpbuild
%define _tmppath /tmp/tmp
%define debug_package %{nil}

Name: %{project}_%{rpmversion}
Version: 1.0.0
Release: 1
Vendor: LHCb
Summary: %{project}
License: GPL
Group: LCG
Source0: %{url}
BuildRoot: %{tmpdir}/%{project}-%{lbversion}-%{cmtconfig}-buildroot
BuildArch: noarch
AutoReqProv: no
Prefix: /opt/lhcb
Provides: /bin/sh


%package -n LCGCMT_preview_ROOT_5.34.05_x86_64_slc6_gcc48_opt
Version:1.0.0
Group:LCG
Summary: LCGCMT LCGCMT_preview_ROOT_5.34.05_x86_64_slc6_gcc48_opt 1.0.0
AutoReqProv: no
Requires: LCGCMT_preview_tcmalloc_1.7p3_x86_64_slc6_gcc48_opt

%package -n LCGCMT_preview_LCGCMT_LCGCMT_preview_x86_64_slc6_gcc48_opt
Version:1.0.0
Group:LCG
Summary: LCGCMT LCGCMT_preview_LCGCMT_LCGCMT_preview_x86_64_slc6_gcc48_opt 1.0.0
AutoReqProv: no

%package -n LCGCMT_preview_tcmalloc_1.7p3_x86_64_slc6_gcc48_opt
Version:1.0.0
Group:LCG
Summary: LCGCMT LCGCMT_preview_tcmalloc_1.7p3_x86_64_slc6_gcc48_opt 1.0.0
AutoReqProv: no

%description
%{project} %{lbversion}


%description -n  LCGCMT_preview_ROOT_5.34.05_x86_64_slc6_gcc48_opt
LCGCMT_preview_ROOT_5.34.05_x86_64_slc6_gcc48_opt 1.0.0

%description -n  LCGCMT_preview_LCGCMT_LCGCMT_preview_x86_64_slc6_gcc48_opt
LCGCMT_preview_LCGCMT_LCGCMT_preview_x86_64_slc6_gcc48_opt 1.0.0

%description -n  LCGCMT_preview_tcmalloc_1.7p3_x86_64_slc6_gcc48_opt
LCGCMT_preview_tcmalloc_1.7p3_x86_64_slc6_gcc48_opt 1.0.0

%prep

%build

%install

cd %_topdir/SOURCES

[ -d ${RPM_BUILD_ROOT} ] && rm -rf ${RPM_BUILD_ROOT}

/bin/mkdir -p ${RPM_BUILD_ROOT}/opt/lhcb/lcg
if [ $? -ne 0 ]; then
  exit $?
fi

cd ${RPM_BUILD_ROOT}/opt/lhcb/lcg
mkdir -p ${RPM_BUILD_ROOT}//opt/lcg/LCGCMT_preview/ROOT/5.34.05/x86_64-slc6-gcc48-opt
rsync -ar %{LCGCMTROOT}/ROOT/5.34.05/x86_64-slc6-gcc48-opt/* ${RPM_BUILD_ROOT}/opt/lcg/LCGCMT_preview/ROOT/5.34.05/x86_64-slc6-gcc48-opt
mkdir -p ${RPM_BUILD_ROOT}//opt/lcg/LCGCMT_preview/LCGCMT/LCGCMT_preview/x86_64-slc6-gcc48-opt
rsync -ar %{LCGCMTROOT}/LCGCMT/LCGCMT_preview/x86_64-slc6-gcc48-opt/* ${RPM_BUILD_ROOT}/opt/lcg/LCGCMT_preview/LCGCMT/LCGCMT_preview/x86_64-slc6-gcc48-opt
mkdir -p ${RPM_BUILD_ROOT}//opt/lcg/LCGCMT_preview/tcmalloc/1.7p3/x86_64-slc6-gcc48-opt
rsync -ar %{LCGCMTROOT}/tcmalloc/1.7p3/x86_64-slc6-gcc48-opt/* ${RPM_BUILD_ROOT}/opt/lcg/LCGCMT_preview/tcmalloc/1.7p3/x86_64-slc6-gcc48-opt


%post

%postun

%clean

%files


%files -n  LCGCMT_preview_ROOT_5.34.05_x86_64_slc6_gcc48_opt
%defattr(-,root,root)
/opt/lcg/LCGCMT_preview/ROOT/5.34.05/x86_64-slc6-gcc48-opt

%files -n  LCGCMT_preview_LCGCMT_LCGCMT_preview_x86_64_slc6_gcc48_opt
%defattr(-,root,root)
/opt/lcg/LCGCMT_preview/LCGCMT/LCGCMT_preview/x86_64-slc6-gcc48-opt

%files -n  LCGCMT_preview_tcmalloc_1.7p3_x86_64_slc6_gcc48_opt
%defattr(-,root,root)
/opt/lcg/LCGCMT_preview/tcmalloc/1.7p3/x86_64-slc6-gcc48-opt


%define date    %(echo `LC_ALL="C" date +"%a %b %d %Y"`)

%changelog

* %{date} User <ben.couturier..rcern.ch>
- first Version


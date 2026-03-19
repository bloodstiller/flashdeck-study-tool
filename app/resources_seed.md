## pass_the_hash
- [HackTricks - Pass the Hash](https://book.hacktricks.xyz/windows-hardening/ntlm/pass-the-hash) - PTH methodology, tools and bypasses
- [Impacket psexec/wmiexec](https://github.com/fortra/impacket) - Python toolset for PTH attacks
- [Mimikatz sekurlsa::pth](https://github.com/gentilkiwi/mimikatz/wiki/module-~-sekurlsa#pth) - Official Mimikatz PTH reference

## credentials
- [Mimikatz Wiki](https://github.com/gentilkiwi/mimikatz/wiki) - Full credential dumping command reference
- [HackTricks - Stealing Credentials](https://book.hacktricks.xyz/windows-hardening/stealing-credentials) - Windows credential dumping techniques
- [CrackStation](https://crackstation.net/) - Online hash cracker with large wordlists
- [Where passwords are stored on Linux/Windows](https://book.hacktricks.xyz/windows-hardening/stealing-credentials/credentials-protections-and-suggestions) - SAM, NTDS, /etc/shadow reference

## sql_injection
- [PortSwigger SQL Injection](https://portswigger.net/web-security/sql-injection) - Interactive labs covering all SQLi types
- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection) - Authoritative OWASP reference
- [PayloadsAllTheThings - SQLi](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/SQL%20Injection) - Payload collection by DB type
- [SQLMap Documentation](https://sqlmap.org/) - Automated SQL injection and takeover tool

## nosql_injection
- [HackTricks - NoSQL Injection](https://book.hacktricks.xyz/pentesting-web/nosql-injection) - NoSQL injection techniques
- [OWASP NoSQL Injection](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05.6-Testing_for_NoSQL_Injection) - Testing guide
- [PayloadsAllTheThings - NoSQL](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/NoSQL%20Injection) - NoSQL payload collection

## xss
- [PortSwigger XSS](https://portswigger.net/web-security/cross-site-scripting) - Interactive XSS labs
- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html) - Prevention and mitigation guide
- [PortSwigger XSS Cheat Sheet](https://portswigger.net/web-security/cross-site-scripting/cheat-sheet) - Filter evasion vectors
- [Content Security Policy Reference](https://content-security-policy.com/) - CSP header implementation guide

## csrf
- [PortSwigger CSRF](https://portswigger.net/web-security/csrf) - Interactive CSRF labs
- [OWASP CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) - Token and SameSite mitigation
- [HackTricks - CSRF](https://book.hacktricks.xyz/pentesting-web/csrf-cross-site-request-forgery) - Exploitation techniques

## ssl_tls
- [SSL Labs SSL Test](https://www.ssllabs.com/ssltest/) - Online TLS configuration checker
- [testssl.sh](https://testssl.sh/) - CLI tool for testing TLS vulnerabilities
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html) - TLS best practices
- [HackTricks - SSL/TLS Vulnerabilities](https://book.hacktricks.xyz/network-services-pentesting/pentesting-ssl) - Heartbleed, POODLE, BEAST, CRIME, DROWN, ROBOT

## heartbleed
- [Heartbleed.com](https://heartbleed.com/) - Official Heartbleed vulnerability explanation
- [OpenSSL Security Advisory](https://www.openssl.org/news/secadv/20140407.txt) - Original OpenSSL advisory
- [HackTricks - Heartbleed](https://book.hacktricks.xyz/network-services-pentesting/pentesting-ssl#heartbleed) - Testing and exploitation

## ssl_tls_attacks
- [POODLE Attack Explained](https://www.openssl.org/~bodo/ssl-poodle.pdf) - Original POODLE research paper
- [BEAST Attack](https://blog.qualys.com/product-tech/2013/09/10/is-beast-still-a-threat) - Is BEAST still a threat?
- [CRIME Attack](https://docs.google.com/presentation/d/11eBmGiX9RqbsqM6fBqBFU-8ocoE6qdU2MUyRxJRCVEk/) - CRIME original presentation
- [DROWN Attack](https://drownattack.com/) - Official DROWN vulnerability site
- [ROBOT Attack](https://robotattack.org/) - Return of Bleichenbacher Oracle Threat

## kerberos
- [HackTricks - Kerberos](https://book.hacktricks.xyz/windows-hardening/active-directory-methodology/kerberos-authentication) - Kerberos attacks overview
- [Harmj0y - Kerberoasting Revisited](https://posts.specterops.io/kerberoasting-revisited-d434351bd4d1) - Deep-dive Kerberoasting
- [Rubeus GitHub](https://github.com/GhostPack/Rubeus) - Kerberos abuse toolkit
- [The Hacker Recipes - Kerberos](https://www.thehacker.recipes/ad/movement/kerberos) - Structured Kerberos attack techniques

## active_directory
- [HackTricks - Active Directory Methodology](https://book.hacktricks.xyz/windows-hardening/active-directory-methodology) - Full AD attack methodology
- [The Hacker Recipes - AD](https://www.thehacker.recipes/ad/movement) - Structured AD attack reference
- [BloodHound Documentation](https://bloodhound.readthedocs.io/) - AD attack path enumeration
- [PayloadsAllTheThings - AD Attacks](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Methodology%20and%20Resources/Active%20Directory%20Attack.md) - AD attack payload collection

## windows_accounts
- [Microsoft - Built-in Accounts](https://docs.microsoft.com/en-us/windows/security/identity-protection/access-control/local-accounts) - Official built-in account documentation
- [HackTricks - Windows Accounts](https://book.hacktricks.xyz/windows-hardening/windows-local-privilege-escalation#users-and-groups) - Account enumeration and exploitation
- [Windows SID Reference](https://docs.microsoft.com/en-us/windows/security/identity-protection/access-control/security-identifiers) - Security Identifier (SID) documentation

## windows_security
- [HackTricks - Windows](https://book.hacktricks.xyz/windows-hardening) - Windows hacking and hardening
- [LOLBAS Project](https://lolbas-project.github.io/) - Living off the land binaries and scripts
- [PayloadsAllTheThings - Windows Privesc](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Methodology%20and%20Resources/Windows%20-%20Privilege%20Escalation.md) - Windows privilege escalation techniques

## smb
- [HackTricks - SMB Pentesting](https://book.hacktricks.xyz/network-services-pentesting/pentesting-smb) - SMB enumeration and exploitation
- [EternalBlue Explained](https://www.avast.com/c-eternalblue) - MS17-010 / WannaCry vulnerability explanation
- [Microsoft SMB Security Best Practices](https://docs.microsoft.com/en-us/windows-server/storage/file-server/smb-security) - Hardening SMB

## null_sessions
- [HackTricks - Null Sessions](https://book.hacktricks.xyz/network-services-pentesting/pentesting-smb#null-session) - Null session enumeration
- [RestrictAnonymous Registry Key](https://support.microsoft.com/en-us/topic/how-to-use-the-restrictanonymous-registry-value-in-windows-2000-and-in-windows-server-2003-8ac341b7-5bba-7e7f-9cf5-b643de80f8b7) - Microsoft KB on RestrictAnonymous

## lm_passwords
- [HackTricks - LM/NTLM Hashes](https://book.hacktricks.xyz/windows-hardening/ntlm) - LM hash weaknesses and cracking
- [LM vs NTLM](https://www.varonis.com/blog/lm-ntlm-net-ntlmv2-oh-my/) - Comparison and security issues

## ftp
- [HackTricks - FTP Pentesting](https://book.hacktricks.xyz/network-services-pentesting/pentesting-ftp) - FTP enumeration and exploitation
- [OWASP FTP Security](https://owasp.org/www-community/vulnerabilities/Cleartext_Transmission_of_Sensitive_Information) - Cleartext transmission risks
- [TFTP Security](https://book.hacktricks.xyz/network-services-pentesting/69-udp-tftp) - TFTP enumeration and file retrieval

## dns
- [HackTricks - DNS](https://book.hacktricks.xyz/network-services-pentesting/pentesting-dns) - DNS enumeration and zone transfers
- [DNSRecon GitHub](https://github.com/darkoperator/dnsrecon) - DNS reconnaissance tool
- [Fierce DNS Scanner](https://github.com/mschwager/fierce) - DNS zone transfer and enumeration tool
- [OWASP DNS Zone Transfer](https://owasp.org/www-community/attacks/Zone_Transfer) - Zone transfer attack explained

## smtp_enumeration
- [HackTricks - SMTP](https://book.hacktricks.xyz/network-services-pentesting/pentesting-smtp) - SMTP enumeration with VRFY EXPN RCPT TO
- [PayloadsAllTheThings - SMTP](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Methodology%20and%20Resources/Network%20Discovery.md) - SMTP user enumeration techniques

## snmp
- [HackTricks - SNMP](https://book.hacktricks.xyz/network-services-pentesting/pentesting-snmp) - SNMP enumeration and community string attacks
- [onesixtyone GitHub](https://github.com/trailofbits/onesixtyone) - SNMP community string scanner
- [SNMP Security Best Practices](https://www.cisecurity.org/insights/blog/snmp-security-best-practices) - Hardening SNMP

## ipsec
- [HackTricks - IPsec](https://book.hacktricks.xyz/network-services-pentesting/ipsec-ike-vpn-pentesting) - IPsec/IKE pentesting
- [Cloudflare - IPsec Explained](https://www.cloudflare.com/learning/network-layer/what-is-ipsec/) - Clear IPsec overview with ESP and AH
- [RFC 4301 - IPsec Architecture](https://datatracker.ietf.org/doc/html/rfc4301) - Official IPsec RFC

## ldap
- [HackTricks - LDAP](https://book.hacktricks.xyz/network-services-pentesting/pentesting-ldap) - LDAP enumeration and attacks
- [PayloadsAllTheThings - LDAP Injection](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/LDAP%20Injection) - LDAP injection payloads

## nmap
- [Nmap Reference Guide](https://nmap.org/book/man.html) - Official Nmap documentation including --source-port
- [HackTricks - Nmap](https://book.hacktricks.xyz/generic-methodologies-and-resources/pentesting-network/nmap-summary-esp) - Nmap techniques and firewall bypass
- [Nmap Cheat Sheet](https://www.stationx.net/nmap-cheat-sheet/) - Quick reference for common Nmap options

## networking_fundamentals
- [OSI Model Explained](https://www.cloudflare.com/learning/ddos/glossary/open-systems-interconnection-model-osi/) - Clear OSI layer explanation
- [TCP/IP DoD Model](https://www.geeksforgeeks.org/tcp-ip-model/) - DoD four-layer model reference
- [Subnetting/CIDR Calculator](https://www.subnet-calculator.com/) - IP and CIDR calculation tool
- [VLANs Explained](https://www.cisco.com/c/en/us/support/docs/lan-switching/vlan/10023-3.html) - Cisco VLAN overview

## arp_attacks
- [HackTricks - ARP Poisoning](https://book.hacktricks.xyz/generic-methodologies-and-resources/pentesting-network/spoofing-llmnr-nbt-ns-mdns-dns-and-wpad-and-relay-attacks) - ARP MITM techniques
- [Ettercap Documentation](https://www.ettercap-project.org/ettercap/) - ARP poisoning and MITM tool
- [ARP Spoofing Defenses](https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst6500/ios/12-2SX/configuration/guide/book/dynarp.html) - Dynamic ARP Inspection

## firewalking
- [Firewalking Technique](https://book.hacktricks.xyz/generic-methodologies-and-resources/pentesting-network/firewall-evasion) - Firewall enumeration and evasion
- [Nmap Firewall Bypass](https://nmap.org/book/man-bypass-firewalls-ids.html) - Source port manipulation and firewalking with Nmap

## wireless
- [HackTricks - WiFi](https://book.hacktricks.xyz/generic-methodologies-and-resources/pentesting-wifi) - WPA/WEP attack methodology
- [Aircrack-ng Documentation](https://www.aircrack-ng.org/documentation.html) - WEP/WPA cracking toolkit
- [WPA Security](https://www.wi-fi.org/discover-wi-fi/security) - Wi-Fi Alliance WPA overview

## cryptography
- [Crypto 101](https://www.crypto101.io/) - Free introductory cryptography textbook
- [OWASP Cryptographic Storage](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html) - Cryptography best practices
- [CryptoPals](https://cryptopals.com/) - Practical cryptography challenges
- [Symmetric vs Asymmetric](https://www.cloudflare.com/learning/ssl/what-is-asymmetric-encryption/) - Clear comparison of encryption types

## hashing
- [HackTricks - Hash Cracking](https://book.hacktricks.xyz/generic-methodologies-and-resources/brute-force#hash-cracking) - Hash identification and cracking
- [Hashcat Documentation](https://hashcat.net/wiki/) - GPU hash cracking reference
- [Hash Identifier](https://www.tunnelsup.com/hash-analyzer/) - Online hash type identifier

## email_security
- [DMARC.org](https://dmarc.org/overview/) - DMARC overview and policy configuration
- [DKIM RFC 6376](https://datatracker.ietf.org/doc/html/rfc6376) - DomainKeys Identified Mail specification
- [MXToolbox DMARC Check](https://mxtoolbox.com/dmarc.aspx) - Test SPF, DKIM and DMARC records
- [OWASP Email Security](https://cheatsheetseries.owasp.org/cheatsheets/Email_Security_Cheat_Sheet.html) - Email security best practices

## cloud_security
- [AWS Security Best Practices](https://aws.amazon.com/security/security-resources/) - AWS security documentation
- [OWASP Cloud Security](https://owasp.org/www-project-cloud-native-application-security-top-10/) - Cloud-native top 10
- [CIS Cloud Benchmarks](https://www.cisecurity.org/cis-benchmarks) - CIS hardening benchmarks for cloud platforms
- [HackTricks - Cloud](https://book.hacktricks.xyz/cloud-security) - Cloud pentesting methodology

## containerization
- [HackTricks - Docker](https://book.hacktricks.xyz/network-services-pentesting/2375-pentesting-docker) - Docker security and breakout techniques
- [HackTricks - Kubernetes](https://book.hacktricks.xyz/cloud-security/pentesting-kubernetes) - Kubernetes security testing
- [Docker Security Docs](https://docs.docker.com/engine/security/) - Official Docker security guidance
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker) - Docker hardening benchmark

## mobile_security
- [OWASP Mobile Security](https://owasp.org/www-project-mobile-security-testing-guide/) - Mobile Security Testing Guide (MSTG)
- [HackTricks - Android](https://book.hacktricks.xyz/mobile-pentesting/android-app-pentesting) - Android APK analysis and testing
- [HackTricks - iOS](https://book.hacktricks.xyz/mobile-pentesting/ios-pentesting) - iOS IPA analysis and jailbreak detection
- [Frida Dynamic Instrumentation](https://frida.re/docs/home/) - Mobile app dynamic analysis toolkit

## bmc_ipmi
- [HackTricks - IPMI](https://book.hacktricks.xyz/network-services-pentesting/623-udp-ipmi) - IPMI enumeration and exploitation
- [IPMI 2.0 Vulnerabilities](https://www.rapid7.com/blog/post/2013/07/02/a-penetration-testers-guide-to-ipmi/) - Rapid7 guide to IPMI attacks
- [Metasploit IPMI Modules](https://github.com/rapid7/metasploit-framework/search?q=ipmi) - IPMI scanner and cipher0 exploit

## ics_ot
- [ICS-CERT Advisories](https://www.cisa.gov/uscert/ics/advisories) - Official ICS vulnerability advisories
- [HackTricks - ICS/SCADA](https://book.hacktricks.xyz/network-services-pentesting/ics-industrial-control-systems) - ICS/SCADA pentesting overview
- [Modbus Security](https://www.dragos.com/resource/modbus-the-protocol-that-wasn-t-designed-for-security/) - Modbus protocol security analysis

## directory_traversal
- [PortSwigger Path Traversal](https://portswigger.net/web-security/file-path-traversal) - Interactive path traversal labs
- [OWASP Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal) - Path traversal attack reference
- [PayloadsAllTheThings - Path Traversal](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Directory%20Traversal) - Traversal payload collection

## session_hijacking
- [PortSwigger Session Management](https://portswigger.net/web-security/authentication/other-mechanisms) - Session fixation and hijacking labs
- [OWASP Session Hijacking](https://owasp.org/www-community/attacks/Session_hijacking_attack) - Session attack techniques
- [HackTricks - Web Session](https://book.hacktricks.xyz/pentesting-web/hacking-with-cookies) - Cookie and session exploitation

## nfs
- [HackTricks - NFS](https://book.hacktricks.xyz/network-services-pentesting/nfs-service-pentesting) - NFS enumeration, mounting and root squashing bypass
- [Root Squashing Explained](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/5/html/deployment_guide/s1-nfs-server-config-exports) - Red Hat NFS exports and root squash

## phishing
- [OWASP Social Engineering](https://owasp.org/www-community/attacks/Phishing) - Phishing attack overview
- [GoPhish Documentation](https://getgophish.com/) - Open source phishing framework
- [NCSC Phishing Guidance](https://www.ncsc.gov.uk/guidance/phishing) - UK NCSC anti-phishing guidance

## enumeration
- [HackTricks - External Recon](https://book.hacktricks.xyz/generic-methodologies-and-resources/external-recon-methodology) - External enumeration methodology
- [SecLists](https://github.com/danielmiessler/SecLists) - Security wordlists for enumeration
- [PayloadsAllTheThings - Methodology](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Methodology%20and%20Resources) - General pentest methodology

## security_standards
- [ISO 27001 Overview](https://www.iso.org/isoiec-27001-information-security.html) - Official ISO 27001 page
- [PCI DSS Documentation](https://www.pcisecuritystandards.org/document_library/) - PCI DSS standard documents
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks) - CIS hardening benchmarks
- [CVSS Calculator](https://www.first.org/cvss/calculator/3.1) - CVSS v3.1 scoring calculator
- [CVE Database](https://cve.mitre.org/) - Official CVE vulnerability database
- [NVD - NIST](https://nvd.nist.gov/) - National Vulnerability Database

## uk_law_and_compliance
- [Computer Misuse Act 1990](https://www.legislation.gov.uk/ukpga/1990/18/contents) - Full text of the CMA
- [Police and Justice Act 2006](https://www.legislation.gov.uk/ukpga/2006/48/contents) - PJA including CMA amendments
- [GDPR - ICO Guidance](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/) - UK ICO GDPR guide
- [RIPA 2000](https://www.legislation.gov.uk/ukpga/2000/23/contents) - Regulation of Investigatory Powers Act
- [Human Rights Act 1998](https://www.legislation.gov.uk/ukpga/1998/42/contents) - Including Article 8 privacy rights

## penetration_testing_scope
- [NCSC CHECK Scheme](https://www.ncsc.gov.uk/information/check-penetration-testing) - CHECK penetration testing requirements
- [PTES - Penetration Testing Standard](http://www.pentest-standard.org/index.php/Main_Page) - Scoping and rules of engagement
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) - Comprehensive web testing methodology

## security_models
- [Bell-LaPadula Model](https://en.wikipedia.org/wiki/Bell%E2%80%93LaPadula_model) - Confidentiality model explanation
- [Biba Integrity Model](https://en.wikipedia.org/wiki/Biba_Model) - Integrity model explanation
- [Clark-Wilson Model](https://en.wikipedia.org/wiki/Clark%E2%80%93Wilson_model) - Commercial integrity model
- [Brewer-Nash (Chinese Wall)](https://en.wikipedia.org/wiki/Brewer_and_Nash_model) - Conflict of interest model

## ransomware
- [NCSC Ransomware Guidance](https://www.ncsc.gov.uk/ransomware/home) - UK NCSC ransomware response guide
- [CISA Ransomware Guide](https://www.cisa.gov/stopransomware) - US CISA ransomware resources
- [Ransomware Response Checklist](https://www.cisecurity.org/insights/white-papers/ransomware-response-checklist) - CIS response checklist

## steganography
- [HackTricks - Steganography](https://book.hacktricks.xyz/crypto-and-stego/stego-tricks) - Stego detection and extraction techniques
- [Steghide Tool](http://steghide.sourceforge.net/) - Steganography tool for images and audio
- [StegOnline](https://stegonline.georgeom.net/upload) - Online steganography analysis tool

## radius_tacacs
- [HackTricks - RADIUS](https://book.hacktricks.xyz/network-services-pentesting/pentesting-radius) - RADIUS authentication testing
- [Cisco TACACS+ Guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_usr_tacacs/configuration/xe-3s/sec-usr-tacacs-xe-3s-book.html) - TACACS+ configuration reference

## oval_cvss
- [OVAL Repository](https://oval.cisecurity.org/) - Open Vulnerability and Assessment Language repository
- [FIRST CVSS Guide](https://www.first.org/cvss/user-guide) - CVSS scoring user guide
- [NVD CVSS Calculator](https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator) - Official CVSS v3 calculator

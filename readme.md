 python3 ptexplorer.py -d atv.pkt outfile
 
 python3 extract_devices_cables.py outfile -o topologia.json


Quero que configure essa topologia da CISCO seguindo os seguintes critérios e instruções. Me de o comando para os roteadores e switches apenas para copiar e colar, com exceção da configuração SSH, que deve ser exibida em parte. Para os PC e Server me mostre as configurações essenciais para o funcionamento da rede e onde configuraçar.


Critérios:


VLAN2 Host 7

VLAN3 Host 8

VLAN4 SERVERDNS

VLAN2 Host 9

VLAN3 Host 10

VLAN4 SERVERHTTP



REITORIA: 30 hosts

PROGEP: 60 hosts

NTI: 6.7.8.10/30

ISP: 6.7.8.9/30

HOST INTERNET: 100.100.100.10/29



VLAN2: 30 hosts

VLAN3: 30 hosts

VLAN4: 14 hosts

VLAN90: 14 hosts 



a) Efetue a criação de sub-redes IPv4 variáveis (VLSM), da Rede 10.40.0.0/24, com a menor perda de endereçamento nos links de WAN e melhor disponibilidade de IP nas LAN’s e mostre todas as sub-redes criadas (utilizadas ou não); Configure a conexão do ISP com a rede Interna para que o HOST INTERNET acesse a rede local;

b) Configure o protocolo de roteamento OSPF, somente no loop; configure o router-id, as interfaces passivas, e redistribua as rotas estáticas/padrão onde for necessário;

c) Configure o DHCP em todos os roteadores (Ele terá que fornecer o IP, máscara de sub-rede, gateway e DNS server; exclua os IPs estáticos;

d) Configure a interface vlan 1 nos switches (REITORIA, PROGEP e NTI) e interface vlan 90 (CCT); configure o default-gateway para permitir o acesso aos switches a partir de redes remotas.

e) Configurar VLAN’s, inclusive a VLAN de gerenciamento (VLAN 90), nos Switches da LAN do CCT colocando cada host em sua respectiva VLAN; A VLAN 90 será utilizada também como nativa. Configure os links de acesso e os de tronco; Configure o Roteamento entre as VLANs no Roteador

f) Configure e ative o serviço do servidor DNS (SERVERDNS); insira a entrada www.engcomp.uema.br paraacessar o serviço HTTP de SERVERHTTP pelo browser. Configure e ative o serviço do servidor WEB;

g) Configurar o SSH em todos os roteadores e switches, use o nome de domínio engcomp.uema.br, username admin, senha adminssh

h) Configurar o Etherchannel entre SW1_CCT e SW2_CCT

i) Configure a senha cisco para acessar o modo privilegiado, para que possa configurar os ativos;

j) Configure os nomes de todos os roteadores, switches e hosts;

k) Conectividade entre todos os hosts, switches e roteadores da Rede;

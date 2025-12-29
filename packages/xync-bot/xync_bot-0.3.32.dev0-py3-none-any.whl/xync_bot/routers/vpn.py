from aiogram import Router, F
from aiogram.types import BufferedInputFile, CallbackQuery
from xync_schema.models import User, Vpn, UserStatus
from os import getenv as env
from dotenv import load_dotenv

from xync_bot.shared import NavCallbackData

load_dotenv()

vpn = Router()


@vpn.callback_query(NavCallbackData.filter(F.to == 'get_vpn'))
async def get_vpn(cbq: CallbackQuery):
    me = cbq.from_user
    if not (u := await User.get_or_none(id=me.id, status__gt=UserStatus.RESTRICTED).prefetch_related('vpn')):
        return await cbq.answer('Этот сервис только для наших доверенных участников. Что бы зарегистрироваться, '
                                'вы должны перейти в бот по пригласительный ссылке от одного из действующих участников сети,'
                                'и дождаться пока он одобрит вашу регистрацию.')
    if not u.vpn:
        try:
            from python_wireguard import Key
            private, public = Key.key_pair()
        except OSError:
            private, public = 'local_test_private_key_'+me.username, 'local_test_public_key_'+me.username
        v = await Vpn.create(priv=private, pub=public, user=u)
    else:
        v = u.vpn
        private = v.priv
    txt = f'''[Interface]
PrivateKey={private}
Address=10.0.0.{v.id}/24
DNS=8.8.8.8
[Peer]
PublicKey={env('SWGPUB')}
AllowedIPs=0.0.0.0/0
Endpoint=vpn.xync.net:51820
PersistentKeepalive=60
'''
    file = BufferedInputFile(txt.encode(), f'XyncVPN_{u.username}.conf')
    caption = 'Import this config file to Wireguard:\n[iOS](https://apps.apple.com/us/app/wireguard/id1441195209)\n' \
              '[Android](https://play.google.com/store/apps/details?id=com.wireguard.android)\n' \
              '[MacOS](https://itunes.apple.com/us/app/wireguard/id1451685025)\n' \
              '[Windows](https://download.wireguard.com/windows-client/wireguard-installer.exe)\n\n' \
              '[Instructions](https://graph.org/VPN-02-19)'
    await cbq.message.answer_document(file, caption=caption)
    await cbq.answer('Your VPN is ready')

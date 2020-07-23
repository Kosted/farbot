import discord


def make_embed(description=None, title=None, author_name=None, author_icon_url=None, footer_text=None, image_url=None,
               thumbnail_url=None, **kwargs):
    embed_obj = discord.Embed(description=description, title=title, colour=discord.Colour.red())
    if author_name and author_icon_url:
        embed_obj.set_author(name=author_name,
                             icon_url=author_icon_url)
    if footer_text:
        embed_obj.set_footer(text=footer_text)
    if image_url:
        embed_obj.set_image(url=image_url)
    if thumbnail_url:
        embed_obj.set_thumbnail(url=thumbnail_url)
    # embed_obj.add_field('name','value',True)
    for field in kwargs:
        embed_obj.add_field(name=field, value=kwargs[field], inline=True)
    return embed_obj


def get_role_by_name(role_name, search_start_point, str_result=False):

    """
    role_like_required = None
    role_name = role_name.lower()

    role_names_list = [role.name.lower() for role in search_start_point]
    for server_role in role_names_list:
        if role_name in server_role:
            if role_name == server_role:
                return role
            else:
                if role_like_required is None:
                    role_like_required = role
    return role_like_required
    """

    role_name = role_name.lower()
    role_like_required = []
    for role in search_start_point:
        if role_name in role.name.lower():
            if role_name == role.name.lower():
                if not str_result:
                    return role
                else:
                    return role.name
            else:
                role_like_required.append(role)
    if len(role_like_required) > 1:
        if not str_result:
            return role_like_required
        else:
            return [role.name for role in role_like_required]
    elif len(role_like_required) == 1:
        if str_result:
            return role_like_required[0].name
        else:
            return role_like_required[0]
    else:
        return role_like_required


def get_nick_or_name(author):
    if author.nick is not None:
        return author.nick
    else:
        return author.name


def hard_prefix_check(prefix, guild_prefixes_set):
    for extend_prefix in guild_prefixes_set:
        if prefix.startswith(extend_prefix) and prefix != extend_prefix:
            print("hard prefix")
            return True
    return False


def list_to_sql_array(value_arr):
    res = '{'

    def to_str(elem):
        if type(elem) is str:
            return '"' + elem + '"'
        else:
            return str(elem)

    value_arr = [to_str(value) for value in value_arr]

    res += ", ".join(value_arr) + '}'

    return res
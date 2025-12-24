def generate_queries(usernames, platform_db):
    queries = []
    for user in usernames:
        for p_name, p_info in platform_db.items():
            # Look for "url" as per your JSON entry
            url_template = p_info.get('url')

            if url_template:
                # Use .format() if you have {} in the URL,
                # or .replace() if you prefer.
                # Your JSON uses {}, so we use .format()
                try:
                    formatted_url = url_template.format(user)
                    queries.append({
                        "username": user,
                        "platform": p_name,
                        "url": formatted_url,
                        "error_type": p_info.get('errorType', 'status_code'),
                        "error_msg": p_info.get('errorMsg', ''),
                        "category": p_info.get('category', 'misc')
                    })
                except IndexError:
                    print(f"[!] Format error in JSON for platform: {p_name}")
            else:
                print(f"[!] skipping {p_name}: missing 'url' key")
    return queries

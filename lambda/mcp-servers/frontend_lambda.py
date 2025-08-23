"""
Frontend MCP Server as Lambda Function
"""
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class FrontendServer:
    """Frontend development guidance and React documentation."""
    
    def __init__(self):
        self.react_docs = {
            'essential-knowledge': {
                'title': 'Essential React Knowledge for AWS Applications',
                'content': '''
# Essential React Knowledge for AWS Applications

## Core Concepts

### Component Architecture
- **Functional Components**: Use hooks for state and lifecycle management
- **Component Composition**: Build complex UIs from simple, reusable components
- **Props and State**: Understand data flow and state management patterns

### State Management
- **useState**: For local component state
- **useReducer**: For complex state logic
- **Context API**: For global state without prop drilling
- **External Libraries**: Redux, Zustand, or Jotai for complex applications

### AWS Integration Patterns
- **API Gateway + Lambda**: RESTful APIs with AWS services
- **Amplify**: Full-stack development platform
- **Cognito**: Authentication and user management
- **S3**: Static hosting and file storage

## Best Practices

### Performance
- Use React.memo() for expensive components
- Implement code splitting with React.lazy()
- Optimize bundle size with tree shaking
- Use React DevTools for performance profiling

### Security
- Sanitize user inputs to prevent XSS
- Use HTTPS for all API communications
- Implement proper authentication flows
- Store sensitive data securely (not in localStorage)

### AWS-Specific Patterns
- Use AWS SDK v3 with tree shaking
- Implement proper error handling for AWS services
- Use AWS Amplify for rapid development
- Follow AWS Well-Architected Framework principles
                '''
            },
            'troubleshooting': {
                'title': 'Common React Issues and Solutions',
                'content': '''
# Common React Issues and Solutions

## State Management Issues

### Problem: State not updating immediately
```javascript
// ❌ Wrong - state updates are asynchronous
const [count, setCount] = useState(0);
setCount(count + 1);
console.log(count); // Still 0

// ✅ Correct - use functional update
setCount(prevCount => {
    console.log(prevCount + 1); // Correct value
    return prevCount + 1;
});
```

### Problem: Infinite re-renders
```javascript
// ❌ Wrong - creates new object on every render
const [user, setUser] = useState({});
useEffect(() => {
    fetchUser().then(setUser);
}, [user]); // This causes infinite loop

// ✅ Correct - proper dependency array
useEffect(() => {
    fetchUser().then(setUser);
}, []); // Empty dependency array for mount only
```

## AWS Integration Issues

### Problem: CORS errors with API Gateway
- Configure CORS properly in API Gateway
- Include credentials in fetch requests if needed
- Use proper HTTP methods (GET, POST, etc.)

### Problem: Authentication with Cognito
- Implement proper token refresh logic
- Handle expired tokens gracefully
- Use AWS Amplify Auth for simplified integration

## Performance Issues

### Problem: Unnecessary re-renders
```javascript
// ❌ Wrong - creates new function on every render
<button onClick={() => handleClick(id)}>Click</button>

// ✅ Correct - use useCallback
const handleClick = useCallback((id) => {
    // handle click
}, []);
```

### Problem: Large bundle sizes
- Use React.lazy() for code splitting
- Implement tree shaking
- Analyze bundle with webpack-bundle-analyzer
- Use AWS CloudFront for CDN delivery
                '''
            }
        }
    
    def get_react_docs_by_topic(self, topic: str) -> Dict[str, Any]:
        """Get React documentation by topic."""
        try:
            if topic not in self.react_docs:
                available_topics = list(self.react_docs.keys())
                return {
                    'success': False,
                    'error': f'Topic "{topic}" not found',
                    'available_topics': available_topics
                }
            
            doc = self.react_docs[topic]
            return {
                'success': True,
                'topic': topic,
                'title': doc['title'],
                'content': doc['content'],
                'format': 'markdown'
            }
            
        except Exception as e:
            logger.error(f"Failed to get React docs for topic {topic}: {e}")
            return {
                'success': False,
                'topic': topic,
                'error': str(e)
            }
    
    def generate_react_component(self, component_name: str, component_type: str = 'functional',
                                props: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate React component template."""
        try:
            props = props or []
            
            if component_type == 'functional':
                # Generate functional component
                props_interface = ""
                if props:
                    props_interface = f"""
interface {component_name}Props {{
{chr(10).join(f'  {prop}: any;' for prop in props)}
}}

"""
                
                props_param = f"{{{', '.join(props)}}}: {component_name}Props" if props else ""
                
                component_code = f"""{props_interface}const {component_name} = ({props_param}) => {{
  return (
    <div className="{component_name.lower()}">
      <h1>{component_name}</h1>
      {chr(10).join(f'      <p>{{props.{prop}}}</p>' for prop in props) if props else '      <p>Component content goes here</p>'}
    </div>
  );
}};

export default {component_name};"""
            
            elif component_type == 'class':
                # Generate class component
                props_interface = ""
                if props:
                    props_interface = f"""
interface {component_name}Props {{
{chr(10).join(f'  {prop}: any;' for prop in props)}
}}

interface {component_name}State {{
  // Add state properties here
}}

"""
                
                component_code = f"""{props_interface}class {component_name} extends React.Component<{component_name}Props{', ' + component_name + 'State' if props else ''}> {{
  constructor(props: {component_name}Props) {{
    super(props);
    this.state = {{}};
  }}

  render() {{
    return (
      <div className="{component_name.lower()}">
        <h1>{component_name}</h1>
        {chr(10).join(f'        <p>{{this.props.{prop}}}</p>' for prop in props) if props else '        <p>Component content goes here</p>'}
      </div>
    );
  }}
}}

export default {component_name};"""
            
            else:
                raise ValueError(f"Unknown component type: {component_type}")
            
            return {
                'success': True,
                'component_name': component_name,
                'component_type': component_type,
                'code': component_code,
                'props': props,
                'language': 'typescript'
            }
            
        except Exception as e:
            logger.error(f"Failed to generate React component: {e}")
            return {
                'success': False,
                'component_name': component_name,
                'error': str(e)
            }
    
    def get_aws_integration_examples(self) -> Dict[str, Any]:
        """Get AWS integration examples for React applications."""
        try:
            examples = {
                'cognito_auth': {
                    'title': 'AWS Cognito Authentication',
                    'description': 'Implement user authentication with AWS Cognito',
                    'code': '''
import { Auth } from 'aws-amplify';

// Sign up
const signUp = async (username: string, password: string, email: string) => {
  try {
    const { user } = await Auth.signUp({
      username,
      password,
      attributes: { email }
    });
    return user;
  } catch (error) {
    console.error('Error signing up:', error);
    throw error;
  }
};

// Sign in
const signIn = async (username: string, password: string) => {
  try {
    const user = await Auth.signIn(username, password);
    return user;
  } catch (error) {
    console.error('Error signing in:', error);
    throw error;
  }
};

// Get current user
const getCurrentUser = async () => {
  try {
    const user = await Auth.currentAuthenticatedUser();
    return user;
  } catch (error) {
    console.error('Not authenticated');
    return null;
  }
};
                    '''
                },
                'api_gateway': {
                    'title': 'API Gateway Integration',
                    'description': 'Call AWS API Gateway endpoints from React',
                    'code': '''
import { API } from 'aws-amplify';

// GET request
const fetchData = async () => {
  try {
    const response = await API.get('myapi', '/items', {});
    return response;
  } catch (error) {
    console.error('Error fetching data:', error);
    throw error;
  }
};

// POST request
const createItem = async (data: any) => {
  try {
    const response = await API.post('myapi', '/items', {
      body: data
    });
    return response;
  } catch (error) {
    console.error('Error creating item:', error);
    throw error;
  }
};

// Custom headers and authentication
const fetchWithAuth = async () => {
  try {
    const response = await API.get('myapi', '/protected', {
      headers: {
        'Authorization': `Bearer ${await Auth.currentSession().then(s => s.getIdToken().getJwtToken())}`
      }
    });
    return response;
  } catch (error) {
    console.error('Error fetching protected data:', error);
    throw error;
  }
};
                    '''
                },
                's3_upload': {
                    'title': 'S3 File Upload',
                    'description': 'Upload files to S3 from React application',
                    'code': '''
import { Storage } from 'aws-amplify';

const FileUpload = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const uploadFile = async () => {
    if (!file) return;

    setUploading(true);
    try {
      const result = await Storage.put(file.name, file, {
        contentType: file.type,
        level: 'public' // or 'private' for user-specific files
      });
      console.log('File uploaded successfully:', result);
    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <input type="file" onChange={handleFileChange} />
      <button onClick={uploadFile} disabled={!file || uploading}>
        {uploading ? 'Uploading...' : 'Upload'}
      </button>
    </div>
  );
};
                    '''
                }
            }
            
            return {
                'success': True,
                'examples': examples,
                'total_examples': len(examples)
            }
            
        except Exception as e:
            logger.error(f"Failed to get AWS integration examples: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Lambda handler for Frontend MCP server."""
    try:
        operation = event.get('operation', 'get_react_docs_by_topic')
        parameters = event.get('parameters', {})
        
        server = FrontendServer()
        
        if operation == 'get_react_docs_by_topic':
            topic = parameters.get('topic', 'essential-knowledge')
            
            results = server.get_react_docs_by_topic(topic)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'documentation': results
                })
            }
        
        elif operation == 'generate_react_component':
            component_name = parameters.get('component_name', '')
            component_type = parameters.get('component_type', 'functional')
            props = parameters.get('props', [])
            
            if not component_name:
                raise ValueError("component_name parameter is required")
            
            results = server.generate_react_component(component_name, component_type, props)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'component': results
                })
            }
        
        elif operation == 'get_aws_integration_examples':
            results = server.get_aws_integration_examples()
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'aws_examples': results
                })
            }
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    except Exception as e:
        logger.error(f"Frontend Lambda error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'operation': event.get('operation', 'unknown')
            })
        }